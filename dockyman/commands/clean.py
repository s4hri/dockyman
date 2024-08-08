import click
import subprocess
from colorama import Fore, Style, init
from dockyman.utils import run_ssh_command
import os
import yaml
from dotenv import load_dotenv

# Initialize colorama
init(autoreset=True)

@click.command(help="Clean Docker images.")
@click.argument('target', required=False, default='both')
@click.argument('host', required=False, default='ssh://localhost')
def clean_command(target, host):
    """Clean Docker images for 'base' and/or 'local' configurations."""

    # Load environment variables from dockyman.env
    load_dotenv('dockyman.env')

    ssh_address = host

    if target == 'base' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Cleaning base images on {host} ***")
        clean_images_from_compose(ssh_address, 'base/compose.yaml')

    if target == 'local' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Cleaning local images on {host} ***")
        clean_images_from_compose(ssh_address, 'local/compose.yaml')

def clean_images_from_compose(host, compose_file):
    """Clean Docker images from services defined in a Docker Compose file."""
    try:
        with open(compose_file, 'r') as file:
            compose_data = yaml.safe_load(file)
            services = compose_data.get('services', {})
            for service in services:
                image_name = services[service].get('image')
                if image_name:
                    # Substitute environment variables in the image name
                    image_name = os.path.expandvars(image_name)
                    remove_docker_image(host, image_name)
                else:
                    click.echo(f"{Fore.RED}Error: No image specified for service '{service}' in {compose_file}")
    except FileNotFoundError:
        click.echo(f"{Fore.RED}Error: {compose_file} not found")
    except yaml.YAMLError as e:
        click.echo(f"{Fore.RED}Error parsing {compose_file}: {e}")

def remove_docker_image(host, image_name):
    """Remove a Docker image."""
    if host == 'localhost':
        command = f"docker image rm --force {image_name}"
    else:
        command = f"DOCKER_HOST={host} docker image rm --force {image_name}"

    click.echo(f"{Fore.LIGHTBLACK_EX}Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            click.echo(f"{Fore.GREEN}Image {image_name} removed successfully.")
        else:
            click.echo(f"{Fore.RED}Error during image removal: {result.stderr}")
    except Exception as e:
        click.echo(f"{Fore.RED}Error during image removal: {e}")
        raise e

if __name__ == "__main__":
    clean_command()
