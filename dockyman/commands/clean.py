import click
import subprocess
import os
from colorama import Fore, Style
from python_on_whales import DockerClient
from dockyman.utils import get_swarm, services_for_nodes
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
        click.echo(f"\n{Fore.CYAN}*** Cleaning base containers ***")
        remove_base(swarm)

    if target == 'local' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Cleaning local containers ***")
        remove_local(swarm)

def remove_base(swarm):
    """Remove base containers using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'base/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')

    services = services_for_nodes(compose_file, swarm, env_file)
    for target_node, service_names in services.items():
        click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Cleaning BASE services {service_names} defined in the compose file: {Fore.WHITE}{compose_file}")
        remove_docker_images(compose_file, env_file, target_node, service_names)


def remove_local(swarm):
    """Remove local containers using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'local/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')

    services = services_for_nodes(compose_file, swarm, env_file)
    for target_node, service_names in services.items():
        if target_node == swarm.manager:
            local_env_file = os.path.join(PREFIX_TARGET, '.env')
        else:
            local_env_file = os.path.join(PREFIX_TARGET, '.env-' + target_node.id)
        click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Cleaning LOCAL services {service_names} in the node: {Fore.WHITE}{target_node.id}")
        remove_docker_images(compose_file, local_env_file, target_node, service_names)


def remove_docker_images(compose_file, env_file, node, services=None):
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_files=[env_file])
    try:
        # Stop and remove the service containers
        res = docker.compose.rm(services=services, stop=True)
        if res:
            click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Stopping services defined in the compose file: {Fore.CYAN}{compose_file}")
            for log_type, log_message in res:
                if isinstance(log_message, tuple):
                    log_message = log_message[1]  # Extract the actual message part of the tuple
                if "server: error reading preface from client" in log_message.decode('utf-8'):
                    continue  # Filter out the specific error message
                if log_type == "stdout":
                    click.echo(f"\t{Fore.LIGHTBLACK_EX}{log_message.decode('utf-8').strip()}")
                elif log_type == "stderr":
                    click.echo(f"\t{Fore.RED}{log_message.decode('utf-8').strip()}", err=True)
            
            click.echo(f"\t{Fore.GREEN} [✓] Service stopped successfully for {compose_file}.")
        
        # Retrieve the Docker Compose project configuration
        project_config = docker.compose.config()
        images = []
        for service_name, service in project_config.services.items():
            images.append(service.image)
        
        if images:
            for image in images:
                # Now, remove the image associated with the service
                click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Removing image {image}) associated with the node: {Fore.WHITE}{node.id}")
                docker.image.remove(image, force=True, prune=True)
                click.echo(f"\t{Fore.GREEN} [✓] Image {image} removed successfully!")
        else:
            click.echo(f"\t{Fore.RED} [x] No image found for node {node.id}")
        
    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Error during remove process: {e}")

if __name__ == "__main__":
    clean_command()
