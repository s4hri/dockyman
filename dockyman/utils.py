import click
import os
import paramiko
import yaml
from urllib.parse import urlparse
import re
from dockyman.config import LOCAL_UID, LOCAL_GID
from colorama import Fore


def resolve_nodes_value(value):
    # Check if the string matches the pattern for an environment variable
    match = re.match(r'\$\{([^}]+)\}', str(value))
    
    if match:
        # Extract the variable name
        variable_name = match.group(1)
        # Try to get the environment variable value, default to the original string if not found
        return os.getenv(variable_name, value)
    else:
        # Return the string as is if it doesn't match the env variable pattern
        return value

class Node:
    def __init__(self, id, host, user, docker_daemon_address, ssh_port):
        self.id = id
        self.host = host
        self.user = user
        self.docker_daemon_address = docker_daemon_address
        self.ssh_port = ssh_port
        self.ssh_address = self.user + '@' + host + ':' + str(ssh_port)

    def __repr__(self):
        return f"<Node(id={self.id}, host={self.host}, user={self.user}, ssh_port={self.ssh_port}, ssh_address={self.ssh_address})>"

class Manager(Node):
    def __init__(self, id, host, user, docker_daemon_address, ssh_port):
        super().__init__(id, host, user, docker_daemon_address, ssh_port)

class Worker(Node):
    def __init__(self, id, host, user, docker_daemon_address, ssh_port):
        super().__init__(id, host, user, docker_daemon_address, ssh_port)

class SwarmConfig:
    def __init__(self, manager, workers):
        self.manager = manager
        self.workers = workers

    @classmethod
    def from_dict(cls, data):

        manager = None
        workers = []

        if 'manager' in data['swarm'].keys(): 
            manager_data = data['swarm']['manager']
            manager = Manager(
                id=str(resolve_nodes_value(manager_data['id'])),
                host=str(resolve_nodes_value(manager_data['host'])),
                user=str(resolve_nodes_value(manager_data['user'])),
                docker_daemon_address=str(resolve_nodes_value(manager_data['docker_daemon_address'])),
                ssh_port=int(resolve_nodes_value(manager_data['ssh_port']))
            )
        if 'workers' in data['swarm'].keys():
            workers = [
                Worker(
                    id=str(resolve_nodes_value(worker['id'])),
                    host=str(resolve_nodes_value(worker['host'])),
                    user=str(resolve_nodes_value(worker['user'])),
                    docker_daemon_address=str(resolve_nodes_value(worker['docker_daemon_address'])),
                    ssh_port=int(resolve_nodes_value(worker['ssh_port']))
                )
                for worker in data['swarm']['workers']
            ]

        return cls(manager=manager, workers=workers)

    def __repr__(self):
        return f"<SwarmConfig(manager={self.manager}, workers={self.workers})>"

    def get_node_from_id(self, node_id):
            # First, check if the manager has the matching ID
            if self.manager and self.manager.id == node_id:
                return self.manager

            # Then, check through the workers list for a matching ID
            for worker in self.workers:
                if worker.id == node_id:
                    return worker

            # If no node is found with the given ID, return None
            return None

def get_swarm(file_path="nodes.yaml"):
    """Load nodes configuration from a YAML file and parse into objects."""
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)

    # Create the SwarmConfig object from the parsed YAML data
    swarm_config = SwarmConfig.from_dict(data)

    return swarm_config

def get_dockyman_version():
    """Reads the version from the dockyman.env file."""
    version = None
    env_file_path = os.path.join(os.path.dirname(__file__), 'model', 'dockyman.env')
    try:
        with open(env_file_path, 'r') as file:
            for line in file:
                if line.startswith("DOCKYMAN_VER="):
                    version = line.split('=')[1].strip()
                    break
    except FileNotFoundError:
        version = "Unknown (dockyman.env not found)"
    if not version:
        version = "Unknown"
    return version

def run_ssh_command(ssh_address, command):
    try:
        """Executes an SSH command on a remote host."""
        url_with_scheme = f"ssh://{ssh_address}"
        url = urlparse(url_with_scheme)
        hostname = url.hostname
        username = url.username
        port = url.port if url.port else 22  # Default to port 22 if not specified

        click.echo(f"{Fore.LIGHTBLACK_EX} Connecting to {hostname} as {username} on port {port} ...")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username, port=port, allow_agent=False)

        click.echo(f"{Fore.LIGHTBLACK_EX} Executing command: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode().strip()
        exit_status = stdout.channel.recv_exit_status()
        click.echo(f"{Fore.LIGHTBLACK_EX} Executing command: {command} {Fore.LIGHTBLACK_EX} Exit status: {exit_status} Command output: {Fore.WHITE} {result}")
        if exit_status != 0:
            error_message = stderr.read().decode().strip()
            click.echo(f"{Fore.YELLOW} Command failed on {hostname}: Error message: {error_message}")
            return False
        ssh.close()
        return result
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        click.echo(f"{Fore.RED} Connection failed to {ssh_address}: {str(e)}")
        return False
    except paramiko.ssh_exception.AuthenticationException as e:
        click.echo(f"{Fore.RED} Authentication failed for {ssh_address}: {str(e)}")
        return False
    except paramiko.ssh_exception.SSHException as e:
        click.echo(f"{Fore.RED} SSH error occurred while connecting to {ssh_address}: {str(e)}")
        return False
    except Exception as e:
        click.echo(f"{Fore.YELLOW}  {str(e)}")
        return False

def load_env_variables(env_file):
    """Load all environment variables from the given .env file."""
    env_vars = {}
    with open(env_file, 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    return env_vars

def generate_env_file(file_path, env_vars):
    """Generate an .env file with the given environment variables."""
    with open(file_path, 'w') as file:
        for key, value in env_vars.items():
            file.write(f"{key}={value}\n")
    os.chown(file_path, LOCAL_UID, LOCAL_GID)

def load_compose_file(compose_file_path):
    with open(compose_file_path, 'r') as file:
        return yaml.safe_load(file)

def services_for_nodes(compose_file, swarm):
    services = {}
    for service_name, service_data in load_compose_file(compose_file).get('services', {}).items():
        target_node = swarm.manager
        labels = service_data.get('labels', {})
        node_label = labels.get('dockyman.node')
        if node_label:
            node = swarm.get_node_from_id(node_id=node_label)
            if node:
                if node != swarm.manager:
                    target_node = node

        if target_node in services.keys():
            services[target_node].append(service_name)
        else:
            services[target_node] = [service_name]
    return services

def services_in_profiles(compose_file, services, active_profiles):
    """Check the services in the compose file and match them with active profiles."""
    services_in_profiles = []
    for service_name, service_data in load_compose_file(compose_file).get("services", {}).items():
        service_profiles = service_data.get("profiles", [])
        if not service_profiles or any(profile in active_profiles for profile in service_profiles):
            if service_name in services:
                services_in_profiles.append(service_name)
    return services_in_profiles
