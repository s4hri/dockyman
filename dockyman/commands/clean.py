import click
import subprocess
import os
from colorama import Fore, Style
from python_on_whales import DockerClient
from dockyman.utils import run_ssh_command, get_swarm, load_env_variables, generate_env_file, get_nodes_for_services
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
        compose_file = os.path.join(PREFIX_TARGET, 'base/compose.yaml')
        services = get_nodes_for_services(compose_file, swarm)
        for service, nodes in services.items():
            for node in nodes:
                click.echo(f"\n{Fore.CYAN}*** Cleaning image {service} on node: {node.id} ***")
                env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')
                remove_docker_compose_service(compose_file, env_file, service, node)

    if target == 'local' or target == 'both':
        compose_file = os.path.join(PREFIX_TARGET, 'local/compose.yaml')
        services = get_nodes_for_services(compose_file, swarm)
        for service, nodes in services.items():
            for node in nodes:
                click.echo(f"\n{Fore.CYAN}*** Cleaning image {service} on node: {node.id} ***")
                if node.role == 'manager':
                    env_file = os.path.join(PREFIX_TARGET, '.env')
                else:
                    env_file = os.path.join(PREFIX_TARGET, f'.env.{node.id}')
                remove_docker_compose_service(compose_file, env_file, service, node)


def remove_docker_compose_service(compose_file, env_file, service, node):
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file)
    
    try:
        # Stop and remove the service containers
        res = docker.compose.rm(services=[service], stop=True)
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
        service_image = project_config.services.get(service).image
        
        if service_image:
            # Now, remove the image associated with the service
            click.echo(f"{Fore.YELLOW}Removing associated image for service: {service} (image: {service_image})...")
            docker.image.remove(service_image, force=True)
            docker.image.prune()
            click.echo(f"{Fore.GREEN}Image {service_image} associated with the service {service} removed successfully.")
        else:
            click.echo(f"{Fore.RED}No image found for service: {service}")
    except Exception as e:
        click.echo(f"{Fore.RED}Error during remove process: {e}")

if __name__ == "__main__":
    clean_command()
