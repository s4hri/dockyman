# MIT License
#
# Copyright (c) 2025 Istituto Italiano di Tecnologia (IIT)
#                    Author: Davide De Tommaso (davide.detommaso@iit.it)
#                    Project: Dockyman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import click
import os
from python_on_whales import DockerClient
from colorama import Fore

from dockyman.config import PREFIX_TARGET
from dockyman.utils import (
    get_swarm,
    services_for_nodes,
    get_dockyman_base_config,
    get_dockyman_local_config
)


@click.command(help="Clean Docker images.")
@click.argument('target', required=False, default='both')
@click.argument('config_file', required=False, default='dockyman.yaml')
def clean_command(target, config_file):
    """Clean Docker images for 'base' and/or 'local' configurations."""
    try:
        config_path = os.path.join(PREFIX_TARGET, config_file)
        swarm = get_swarm(config_path)
    except FileNotFoundError:
        click.echo(f"{Fore.YELLOW}[x] Error: Config file not found.")
        raise click.Abort()

    if target in ('base', 'both'):
        click.echo(f"\n{Fore.CYAN}*** Cleaning BASE containers ***")
        compose_file, env_file = get_dockyman_base_config(config_path)
        clean_target(swarm, compose_file, env_file, context='base')

    if target in ('local', 'both'):
        click.echo(f"\n{Fore.CYAN}*** Cleaning LOCAL containers ***")
        compose_file = get_dockyman_local_config(config_path)
        env_file = os.path.join(PREFIX_TARGET, '.env')  # fallback for manager
        clean_target(swarm, compose_file, env_file, context='local')


def clean_target(swarm, compose_file, base_env_file, context):
    """Generic cleaner for base/local contexts."""
    services = services_for_nodes(compose_file, swarm, base_env_file)

    for node, service_names in services.items():
        # Select correct env file for local mode
        if context == 'local':
            env_file = os.path.join(PREFIX_TARGET, f'.env-{node.id}')
            if not os.path.isfile(env_file):
                env_file = base_env_file
        else:
            env_file = base_env_file

        click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Cleaning {context.upper()} services {service_names} for node: {Fore.WHITE}{node.id}")
        remove_docker_images(compose_file, env_file, node, service_names)


def remove_docker_images(compose_file, env_file, node, services=None):
    docker = DockerClient(
        host=node.docker_daemon_address,
        compose_files=[compose_file],
        compose_env_files=[env_file]
    )

    try:
        # Stop and remove service containers
        res = docker.compose.rm(services=services, stop=True)
        if res:
            click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Removing stopped containers from {compose_file}")
            for log_type, log_message in res:
                log_message = log_message[1] if isinstance(log_message, tuple) else log_message
                text = log_message.decode('utf-8').strip()
                if "server: error reading preface from client" in text:
                    continue
                color = Fore.LIGHTBLACK_EX if log_type == "stdout" else Fore.RED
                click.echo(f"\t{color}{text}", err=(log_type == "stderr"))

            click.echo(f"\t{Fore.GREEN} [✓] Containers removed for node {node.id}.")

        # Remove images
        project_config = docker.compose.config()
        images = [service.image for service in project_config.services.values() if service.image]

        if images:
            for image in images:
                click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Removing image {image} from node: {Fore.WHITE}{node.id}")
                docker.image.remove(image, force=True, prune=True)
                click.echo(f"\t{Fore.GREEN} [✓] Image {image} removed successfully!")
        else:
            click.echo(f"\t{Fore.YELLOW} [!] No images found to remove on node {node.id}")

    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Error removing containers or images: {e}")


if __name__ == "__main__":
    clean_command()
