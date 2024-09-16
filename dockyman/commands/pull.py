import click
import os
from python_on_whales import DockerClient
from colorama import Fore
from dockyman.utils import get_swarm, services_for_nodes
from dockyman.config import PREFIX_TARGET

@click.command(help="Pull Docker images.")
@click.argument('nodes_file', required=False, default='nodes.yaml')
def pull_command(nodes_file):
    """Pull Docker Base images."""

    swarm = None
    try:
        nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
        swarm = get_swarm(nodes_file_path)
    except FileNotFoundError:
        click.echo(f"{Fore.YELLOW}Error: Nodes configuration file not found.")
        return

    pull_base(swarm)

def pull_base(swarm):
    """Pull base images using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'base/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')

    services = services_for_nodes(compose_file, swarm)
    for target_node, service_names in services.items():
        click.echo(f"{Fore.CYAN}*** Pulling BASE services {service_names} on {target_node.id} ***")
        pull_docker_images(compose_file, env_file, target_node, service_names)
        

def pull_docker_images(compose_file, env_file, node, services=None):
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file)
    try:
        docker.compose.pull(services=services)
    except Exception as e:
        click.echo(f"{Fore.RED}Error during the pull process: {e}")

if __name__ == "__main__":
    pull_command()
