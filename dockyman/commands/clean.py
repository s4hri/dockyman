import click
import subprocess
import os
from colorama import Fore, Style
from python_on_whales import DockerClient
from dockyman.utils import get_swarm, load_compose_file
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
        click.echo(f"{Fore.LIGHTBLACK_EX}Running on {target_node.id}: docker compose -f {compose_file} --env-file {env_file} rm ")
        remove_docker_images(compose_file, env_file, target_node)



def remove_local(swarm):
    """Remove local containers using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'local/compose.yaml')

    services = load_compose_file(compose_file).get('services', {})
    for service_name, service_data in services.items():
        target_node = swarm.manager
        local_env_file = os.path.join(PREFIX_TARGET, '.env')
        labels = service_data.get('labels', {})
        node_label = labels.get('dockyman.node')
        if node_label:
            node = swarm.get_node_from_id(node_id=node_label)
            if node:
                if node != swarm.manager:
                    target_node = node
                    local_env_file = os.path.join(PREFIX_TARGET, '.env-' + target_node.id)

        click.echo(f"{Fore.LIGHTBLACK_EX}Running on {target_node.id}: docker compose -f {compose_file} --env-file {local_env_file} rm")
        remove_docker_images(compose_file, local_env_file, target_node)

def remove_docker_images(compose_file, env_file, node):
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file)
    
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
