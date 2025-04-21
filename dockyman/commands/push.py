import click
import os
from python_on_whales import DockerClient
from colorama import Fore, Style
from dockyman.utils import get_swarm, services_for_nodes
from dockyman.config import PREFIX_TARGET

@click.command(help="Push Docker images.")
@click.argument('nodes_file', required=False, default='nodes.yaml')
def push_command(nodes_file):
    """Push Docker Base images."""

    swarm = None
    try:
        nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
        swarm = get_swarm(nodes_file_path)
    except FileNotFoundError:
        click.echo(f"{Fore.YELLOW}Error: Nodes configuration file not found.")

    push_base(swarm)

def push_base(swarm):
    """Push base images using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'base/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')

    services = services_for_nodes(compose_file, swarm)
    for target_node, service_names in services.items():        
        click.echo(f"{Fore.CYAN}*** Pushing BASE services {service_names} on {target_node.id} ***")
        push_docker_images(compose_file, env_file, target_node, service_names)

def push_docker_images(compose_file, env_file, node, services=None):
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_files=[env_file])
    try:
        docker.compose.push(services=services)
    except Exception as e:
        click.echo(f"{Fore.RED}Error during the push process: {e}")

if __name__ == "__main__":
    push_command()
