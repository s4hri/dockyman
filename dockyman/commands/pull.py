import click
import os
from python_on_whales import DockerClient
from colorama import Fore, Style
from dockyman.utils import get_swarm, load_compose_file
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

    services = load_compose_file(compose_file).get('services', {})
    for service_name, service_data in services.items():
        target_node = swarm.manager
        labels = service_data.get('labels', {})
        node_label = labels.get('dockyman.node')
        if node_label:
            node = swarm.get_node_from_id(node_id=node_label)
            if node:
                if node != swarm.manager:
                    target_node = node
        
        click.echo(f"{Fore.LIGHTBLACK_EX}Running on {target_node.id}: docker compose -f {compose_file} --env-file {env_file} pull")
        pull_docker_images(compose_file, env_file, target_node)

def pull_docker_images(compose_file, env_file, node):
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file)

    try:
        # Retrieve the Docker Compose project configuration
        project_config = docker.compose.config()
        images = []
        for service_name, service in project_config.services.items():
            images.append(service.image)
        
        if images:
            for image in images:
                tag = image
                click.echo(f"{Fore.YELLOW}Pulling image {tag} associated with node {node.id} ...")
                
                docker.image.pull(tag)
                click.echo(f"{Fore.GREEN}Image {tag} pulled successfully!")
        else:
            click.echo(f"{Fore.RED}No image found for node {node.id}")

    except Exception as e:
        click.echo(f"{Fore.RED}Error during pull process: {e}")

if __name__ == "__main__":
    pull_command()
