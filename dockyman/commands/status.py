import os
import click
from python_on_whales import DockerClient
from colorama import Fore
from dockyman.config import PREFIX_TARGET
from dockyman.utils import get_swarm, run_ssh_command, Node


@click.command()
@click.argument('nodes_file', required=False, default='nodes.yaml')
@click.option('--ssh_address', required=False)
@click.option('--docker_daemon_address', required=False)
def status_command(nodes_file, ssh_address, docker_daemon_address):
    """Check the status of the Docker Swarm nodes defined in the config file."""

    if ssh_address or docker_daemon_address:
        if ssh_address:
            check_ssh_connection(ssh_address)
        if docker_daemon_address:
            check_docker_daemon(docker_daemon_address)
    else:
        try:
            nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
            swarm = get_swarm(nodes_file_path)

            # Check the manager node
            click.echo(f"{Fore.CYAN}*** Checking Manager Node: {swarm.manager.id} ***")
            check_node(swarm.manager)

            # Check the worker nodes
            for worker in swarm.workers:
                click.echo(f"{Fore.CYAN}*** Checking Worker Node: {worker.id} ***")
                check_node(worker)
        except Exception as e:
            click.echo(f"{Fore.RED} Please provide a valid nodes file path or options.")


def check_node(node: Node):
    """Check the SSH connection and Docker daemon for a given node."""
    check_ssh_connection(node.ssh_address)
    check_docker_daemon(node.docker_daemon_address)

def check_ssh_connection(ssh_address):
    """Check if the SSH connection with the provided address is working."""
    click.echo(f"\n{Fore.WHITE} -> Checking SSH connection with: {ssh_address} ...")
    ssh_status = run_ssh_command(ssh_address, "echo 'SSH connection test'")

    if ssh_status:
        click.echo(f"\t{Fore.GREEN} [✓] SSH connection to {ssh_address} is successful!")
        return True
    else:
        click.echo(f"\t{Fore.RED} [x] Failed to connect via SSH to {ssh_address}.")
        return False

def check_docker_daemon(docker_daemon_address):
    """Check if the Docker daemon is responding using python-on-whales."""
    click.echo(f"\n{Fore.WHITE} -> Checking Docker Daemon: {docker_daemon_address} ...")

    try:
        # Initialize DockerClient with the appropriate host
        docker = DockerClient(host=docker_daemon_address)

        # Retrieve Docker version to verify the connection
        version_info = docker.version()
        click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Docker Version in your system: {version_info.server.version}")
        click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Docker Version in current Dockyman: {version_info.client.version}")
        click.echo(f"\t{Fore.GREEN} [✓] Docker daemon at {docker_daemon_address} is responding!")
        return True

    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Docker Daemon Error: {str(e)}")
        click.echo(f"\t{Fore.RED} [x] Failed to connect to Docker daemon at {docker_daemon_address}.")
        return False

if __name__ == '__main__':
    status_command()
