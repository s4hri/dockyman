import click
import subprocess
import os
from colorama import Fore, Style
from python_on_whales import DockerClient
from dockyman.utils import run_ssh_command, get_swarm, load_env_variables, generate_env_file
from dockyman.config import PREFIX_TARGET


@click.command(help="Clean Docker images.")
@click.argument('target', required=False, default='both')
@click.argument('nodes_file', required=False, default='nodes.yaml')
def clean_command(target, nodes_file):
    """Clean Docker images for 'base' and/or 'local' configurations."""

    swarm = None
    try:
        nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
        swarm = get_swarm(nodes_file_path)
    except FileNotFoundError:
        click.echo(f"{Fore.YELLOW}Error: Nodes configuration file not found.")

    if target == 'base' or target == 'both':
        remove_base(swarm)

    if target == 'local' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Building local containers ***")
        remove_local(swarm)

def remove_base(swarm):
    """Remove base containers using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'base/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')
    click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} --profile {swarm.manager.id} rm")

    remove_docker_images(compose_file, env_file, swarm.manager.id, swarm.manager)

    for worker in swarm.workers:
        click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} --profile {worker.id} rm")
        remove_docker_images(compose_file, env_file, worker.id, worker)

def remove_local(swarm):
    """Remove local containers using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'local/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, '.env')
    remove_docker_images(compose_file, env_file, swarm.manager.id, swarm.manager)

    for worker in swarm.workers:
        env_file = os.path.join(PREFIX_TARGET, '.env-' + worker.id)
        click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} --profile {worker.id} rm")
        remove_docker_images(compose_file, env_file, worker.id, worker)

def remove_docker_images(compose_file, env_file, profile, node):
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file, compose_profiles=[profile])
    
    try:
        # Stop and remove the service containers
        res = docker.compose.rm(stop=True)
        if res:
            for log_type, log_message in res:
                if isinstance(log_message, tuple):
                    log_message = log_message[1]  # Extract the actual message part of the tuple
                if "server: error reading preface from client" in log_message.decode('utf-8'):
                    continue  # Filter out the specific error message
                if log_type == "stdout":
                    click.echo(f"{Fore.LIGHTBLACK_EX}{log_message.decode('utf-8').strip()}")
                elif log_type == "stderr":
                    click.echo(f"{Fore.RED}{log_message.decode('utf-8').strip()}", err=True)
            
            click.echo(f"{Fore.GREEN}Service removed successfully for {compose_file}.")
        
        # Retrieve the Docker Compose project configuration
        project_config = docker.compose.config()
        images = []
        for service_name, service in project_config.services.items():
            images.append(service.image)
        
        if images:
            for image in images:
                # Now, remove the image associated with the service
                click.echo(f"{Fore.YELLOW}Removing image {image}) associated with node {node.id} ...")
                docker.image.remove(image, force=True, prune=True)
                click.echo(f"{Fore.GREEN}Image {image} removed successfully!")
        else:
            click.echo(f"{Fore.RED}No image found for node {node.id}")
        
    except Exception as e:
        click.echo(f"{Fore.RED}Error during remove process: {e}")

if __name__ == "__main__":
    clean_command()
