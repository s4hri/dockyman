import click
import os
from python_on_whales import DockerClient
from colorama import Fore, Style
from dockyman.utils import get_swarm
from dockyman.config import PREFIX_TARGET

@click.command(help="Pull Docker images.")
@click.argument('nodes_file', required=False, default='nodes.yaml')
@click.argument('registry', required=False, default='')
def pull_command(nodes_file, registry):
    """Pull Docker Base images."""

    swarm = None
    try:
        nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
        swarm = get_swarm(nodes_file_path)
    except FileNotFoundError:
        click.echo(f"{Fore.YELLOW}Error: Nodes configuration file not found.")
        return

    pull_base(swarm, registry)

def pull_base(swarm, registry):
    """Pull base images using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'base/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')
    click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} --profile {swarm.manager.id} pull")

    pull_docker_images(compose_file, env_file, swarm.manager.id, swarm.manager, registry)

    for worker in swarm.workers:
        click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} --profile {worker.id} pull")
        pull_docker_images(compose_file, env_file, worker.id, worker, registry)

def pull_docker_images(compose_file, env_file, profile, node, registry):
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file, compose_profiles=[profile])

    try:
        # Retrieve the Docker Compose project configuration
        project_config = docker.compose.config()
        images = []
        for service_name, service in project_config.services.items():
            images.append(service.image)
        
        if images:
            for image in images:
                # Construct the full image path including registry
                tag = f"{registry}/{image}" if registry else image
                click.echo(f"{Fore.YELLOW}Pulling image {tag} associated with node {node.id} ...")
                
                # Now, pull the image from the registry
                docker.image.pull(tag)
                click.echo(f"{Fore.GREEN}Image {tag} pulled successfully!")
        else:
            click.echo(f"{Fore.RED}No image found for node {node.id}")

    except Exception as e:
        click.echo(f"{Fore.RED}Error during pull process: {e}")

if __name__ == "__main__":
    pull_command()
