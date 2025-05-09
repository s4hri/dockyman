# MIT License
#
# Copyright (c) 2025 Istituto Italiano di Tecnologia (IIT)
#                    Author: Davide De Tommaso (davide.detommaso@iit.it)
#                    Project: Dockyman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import click
import os
import paramiko
import yaml
import re
from urllib.parse import urlparse
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

def get_swarm(file_path=None):
    """
    Load swarm configuration from dockyman.yaml and return SwarmConfig object.
    """
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "model", "dockyman.yaml")

    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)

    return SwarmConfig.from_dict(config)

def get_dockyman_version():
    """
    Reads the dockyman_version from the dockyman.yaml file.
    """
    yaml_path = os.path.join(os.path.dirname(__file__), 'model', 'dockyman.yaml')

    try:
        with open(yaml_path, 'r') as file:
            config = yaml.safe_load(file)
            return config.get("project", {}).get("dockyman_version", "Unknown")
    except FileNotFoundError:
        return "Unknown (dockyman.yaml not found)"
    except Exception as e:
        return f"Unknown (error reading dockyman.yaml: {e})"

def get_dockyman_base_config(config_filepath):
    """
    Parses the build.env YAML file and returns absolute paths
    for the base build compose_file and env_file.

    Args:
        config_filepath (str): Path to the dockyman.env YAML file.

    Returns:
        (str, str): Tuple of (compose_file_path, env_file_path)
    """
    with open(config_filepath, "r") as f:
        config = yaml.safe_load(f)

    try:
        base_config = config["project"]["build"]["base"]
        compose_path = os.path.normpath(os.path.join(os.path.dirname(config_filepath), base_config["compose_file"]))
        env_path = os.path.normpath(os.path.join(os.path.dirname(config_filepath), base_config["env_file"]))
        return compose_path, env_path
    except KeyError as e:
        raise ValueError(f"Missing expected key in dockyman.env: {e}")

def get_dockyman_local_config(config_filepath):
    """
    Parses the dockyman.yaml YAML file and returns absolute paths
    for the local build compose_file and env_file.

    Args:
        config_filepath (str): Path to the dockyman.env YAML file.

    Returns:
        (str, str): Tuple of (compose_file_path, env_file_path)
    """
    with open(config_filepath, "r") as f:
        config = yaml.safe_load(f)

    try:
        local_config = config["project"]["build"]["local"]
        compose_path = os.path.normpath(os.path.join(os.path.dirname(config_filepath), local_config["compose_file"]))
        return compose_path
    except KeyError as e:
        raise ValueError(f"Missing expected key in dockyman.env: {e}")

def get_dockyman_runtime_config(config_filepath):
    """
    Parses the dockyman.yaml YAML file and returns absolute paths
    for the runtime compose_file and env_file.

    Args:
        config_filepath (str): Path to the dockyman.env YAML file.

    Returns:
        (str, str): Tuple of (compose_file_path, env_file_path)
    """
    with open(config_filepath, "r") as f:
        config = yaml.safe_load(f)

    try:
        runtime_config = config["project"]["runtime"]
        compose_path = os.path.normpath(os.path.join(os.path.dirname(config_filepath), runtime_config["compose_file"]))
        env_path = os.path.normpath(os.path.join(os.path.dirname(config_filepath), runtime_config["env_file"]))
        return compose_path, env_path
    except KeyError as e:
        raise ValueError(f"Missing expected key in dockyman.env: {e}")

def run_ssh_command(ssh_address, command):
    try:
        """Executes an SSH command on a remote host."""
        url_with_scheme = f"ssh://{ssh_address}"
        url = urlparse(url_with_scheme)
        hostname = url.hostname
        username = url.username
        port = url.port if url.port else 22  # Default to port 22 if not specified

        click.echo(f"\t{Fore.LIGHTBLACK_EX}[.] Connecting to {hostname} as {username} on port {port} ...")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username, port=port, allow_agent=False)

        click.echo(f"\t{Fore.LIGHTBLACK_EX}[.] Executing command: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode().strip()
        exit_status = stdout.channel.recv_exit_status()
        click.echo(f"\t{Fore.LIGHTBLACK_EX}[.] Executing command: {command} {Fore.LIGHTBLACK_EX} Exit status: {exit_status} Command output: {Fore.WHITE} {result}")
        if exit_status != 0:
            error_message = stderr.read().decode().strip()
            click.echo(f"\t{Fore.YELLOW}[.] Command failed on {hostname}: Error message: {error_message}")
            return False
        ssh.close()
        return result
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        click.echo(f"\t{Fore.RED}[x] Connection failed to {ssh_address}: {str(e)}")
        return False
    except paramiko.ssh_exception.AuthenticationException as e:
        click.echo(f"\t{Fore.RED}[x] Authentication failed for {ssh_address}: {str(e)}")
        return False
    except paramiko.ssh_exception.SSHException as e:
        click.echo(f"\t{Fore.RED}[x] SSH error occurred while connecting to {ssh_address}: {str(e)}")
        return False
    except Exception as e:
        click.echo(f"\t{Fore.YELLOW}[!]  {str(e)}")
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

def services_for_nodes(compose_file, swarm, env_file=None):
    services = {}
    
    for service_name, service_data in load_compose_file(compose_file).get('services', {}).items():
        service_profiles = service_data.get("profiles", [])
        env_profiles = get_docker_profiles(env_file)

        # Check if the service has profiles
        if service_profiles:
            # Check if any of the service profiles match the active profiles
            if any(profile in env_profiles for profile in service_profiles):

                for profile in service_profiles:
                    # if profile corresponds to a node id then add the serviece to the node
                    node = swarm.get_node_from_id(node_id=profile)
                    if node:
                        target_node = node
                        if target_node not in services.keys():
                            services[target_node] = []
                        services[target_node].append(service_name)
        else:
            if target_node not in services.keys():
                services[target_node] = []
            services[target_node].append(service_name)
    return services

def services_in_profiles(compose_file, active_profiles):
    """Check the services in the compose file and match them with active profiles."""
    services_in_profiles = []
    for service_name, service_data in load_compose_file(compose_file).get("services", {}).items():
        service_profiles = service_data.get("profiles", [])
        if not service_profiles or any(profile in active_profiles for profile in service_profiles):
            services_in_profiles.append(service_name)
    return services_in_profiles


def get_docker_profiles(env_file):
    """Get the selected docker profiles from the .env file."""
    env_vars = load_env_variables(env_file)
    profiles = []
    if "COMPOSE_PROFILES" in env_vars.keys():
        profiles = env_vars["COMPOSE_PROFILES"].split(',')
    return profiles


def load_extra_env_vars_from_dockyman(config_path):
    """
    Load extra environment variables from 'environments_extra' in dockyman.yaml.

    Returns:
        dict: {VAR: VALUE} parsed from list of 'KEY=VALUE' strings.
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        extras = config.get("environments_extra", [])
        extra_vars = {}

        for item in extras:
            if '=' in item:
                key, value = item.split('=', 1)
                extra_vars[key.strip()] = value.strip()

        return extra_vars
    except Exception as e:
        raise RuntimeError(f"Failed to parse environments_extra: {e}")