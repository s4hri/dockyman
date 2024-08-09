import os
import yaml
import click
import paramiko
import requests
from urllib.parse import urlparse
from python_on_whales import DockerClient
from config import PREFIX_TARGET, LOCAL_GID, LOCAL_UID, LOCAL_USERNAME

# Import colorama for colored output
from colorama import Fore, Style


@click.command()
@click.argument('config_file', default='nodes.yaml')
def status_command(config_file):
    """Check the status of the Docker Swarm nodes defined in the config file."""

    config_file_path = os.path.join(PREFIX_TARGET, config_file)
    
    # Load the configuration file
    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)

    # Check the manager node
    check_node(config['swarm']['manager'])

    # Check the worker nodes
    for worker in config['swarm']['workers']:
        check_node(worker)

def check_node(node):
    """Check the SSH connection and Docker daemon for a given node."""
    click.echo(f"\n{Fore.CYAN}*** Checking node: {node['hostname']} ***")
    
    ssh_status = check_ssh_connection(node['ssh_address'])
    if ssh_status:
        click.echo(f"{Fore.GREEN}SSH connection to {node['ssh_address']} is successful.")
    else:
        click.echo(f"{Fore.RED}Failed to connect via SSH to {node['ssh_address']}.")

    docker_status = check_docker_daemon(node['docker_daemon_address'])
    if docker_status:
        click.echo(f"{Fore.GREEN}Docker daemon at {node['docker_daemon_address']} is responding.")
    else:
        click.echo(f"{Fore.RED}Failed to connect to Docker daemon at {node['docker_daemon_address']}.")

def check_ssh_connection(ssh_address):
    """Check if the SSH connection to the node is successful."""
    try:
        url = urlparse(ssh_address)
        hostname = url.hostname or 'localhost'
        username = url.username or LOCAL_USERNAME
        port = url.port or 22

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username, port=port)
        ssh.close()
        return True
    except Exception as e:
        click.echo(f"{Fore.RED}SSH Error: {str(e)}")
        return False

def check_docker_daemon(docker_daemon_address):
    """Check if the Docker daemon is responding using python-on-whales."""
    try:
        # Initialize DockerClient with the appropriate host
        docker = DockerClient(host=docker_daemon_address)

        # Retrieve Docker version to verify the connection
        version_info = docker.version()
        click.echo(f"Docker Version: {version_info}")
        return True

    except Exception as e:
        click.echo(f"{Fore.RED}Docker Daemon Error: {str(e)}")
        return False

if __name__ == '__main__':
    status_command()
