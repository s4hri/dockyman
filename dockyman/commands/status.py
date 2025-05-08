import os
import click
from python_on_whales import DockerClient
from colorama import Fore
from dockyman.config import PREFIX_TARGET
from dockyman.utils import get_swarm, run_ssh_command, Node


@click.command()
@click.argument('config_file', required=False, default='dockyman.yaml')
@click.option('--ssh_address', help='Directly test an SSH address', required=False)
@click.option('--docker_daemon_address', help='Directly test a Docker daemon address', required=False)
def status_command(config_file, ssh_address, docker_daemon_address):
    """
    Check the status of Docker Swarm nodes defined in the dockyman.yaml config,
    or test specific addresses directly using --ssh_address / --docker_daemon_address.
    """
    if ssh_address or docker_daemon_address:
        if ssh_address:
            check_ssh_connection(ssh_address)
        if docker_daemon_address:
            check_docker_daemon(docker_daemon_address)
    else:
        config_path = os.path.join(PREFIX_TARGET, config_file)

        try:
            swarm = get_swarm(config_path)

            click.echo(f"{Fore.CYAN}*** Checking Manager Node: {swarm.manager.id} ***")
            check_node(swarm.manager)

            for worker in swarm.workers:
                click.echo(f"{Fore.CYAN}*** Checking Worker Node: {worker.id} ***")
                check_node(worker)

        except Exception as e:
            click.echo(f"{Fore.RED}[x] Error: {e}")
            click.echo(f"{Fore.RED}[x] Could not load or parse config file: {config_path}")


def check_node(node: Node):
    """Run full check (SSH + Docker) for a single node."""
    check_ssh_connection(node.ssh_address)
    check_docker_daemon(node.docker_daemon_address)


def check_ssh_connection(ssh_address):
    """Test SSH connectivity to a node."""
    click.echo(f"\n{Fore.WHITE} -> Checking SSH connection with: {ssh_address} ...")
    ssh_status = run_ssh_command(ssh_address, "echo 'SSH connection test'")

    if ssh_status:
        click.echo(f"\t{Fore.GREEN}[✓] SSH connection to {ssh_address} successful!")
        return True
    else:
        click.echo(f"\t{Fore.RED}[x] SSH connection to {ssh_address} failed.")
        return False


def check_docker_daemon(docker_daemon_address):
    """Test Docker daemon accessibility via python-on-whales."""
    click.echo(f"\n{Fore.WHITE} -> Checking Docker Daemon: {docker_daemon_address} ...")

    try:
        docker = DockerClient(host=docker_daemon_address)
        version_info = docker.version()
        click.echo(f"\t{Fore.LIGHTBLACK_EX}[.] Host Docker version: {version_info.server.version}")
        click.echo(f"\t{Fore.LIGHTBLACK_EX}[.] Client Docker version: {version_info.client.version}")
        click.echo(f"\t{Fore.GREEN}[✓] Docker daemon at {docker_daemon_address} is responding!")
        return True
    except Exception as e:
        click.echo(f"\t{Fore.RED}[x] Docker Daemon Error: {str(e)}")
        return False


if __name__ == '__main__':
    status_command()
