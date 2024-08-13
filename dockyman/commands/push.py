import click
import os
from python_on_whales import DockerClient
from colorama import Fore, Style
from dockyman.utils import get_swarm, load_env_variables
from dockyman.config import PREFIX_TARGET

@click.command(help="Push Docker images.")
@click.argument('nodes_file', required=False, default='nodes.yaml')
@click.argument('registry', required=False, default='')
def push_command(nodes_file, registry):
    """Push Docker Base images."""

    swarm = None
    try:
        nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
        swarm = get_swarm(nodes_file_path)
    except FileNotFoundError:
        click.echo(f"{Fore.YELLOW}Error: Nodes configuration file not found.")

    push_base(swarm, registry)

def push_base(swarm, registry):
    """Push base images using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'base/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')
    click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} --profile {swarm.manager.id} push")

    push_docker_images(compose_file, env_file, swarm.manager.id, swarm.manager, registry)

    for worker in swarm.workers:
        click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} --profile {worker.id} push")
        push_docker_images(compose_file, env_file, worker.id, worker, registry)


def push_docker_images(compose_file, env_file, profile, node, registry):
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file, compose_profiles=[profile])

    try:
        # Retrieve the Docker Compose project configuration
        project_config = docker.compose.config()
        images = []
        for service_name, service in project_config.services.items():
            images.append(service.image)
        
        if images:
            for image in images:
                # Tag the image with the registry name
                #tag = f"{registry}/{image}"
                tag = f"{image}"
                docker.image.tag(image, tag)
                click.echo(f"{Fore.YELLOW}Pushing image {tag} associated with node {node.id} ...")
                
                # Now, push the tagged image to the registry
                docker.image.push(tag)
                click.echo(f"{Fore.GREEN}Image {tag} pushed successfully!")
        else:
            click.echo(f"{Fore.RED}No image found for node {node.id}")

    except Exception as e:
        click.echo(f"{Fore.RED}Error during push process: {e}")

if __name__ == "__main__":
    push_command()
