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

import os
import click
from python_on_whales import DockerClient
from colorama import Fore

from dockyman.utils import (
    get_swarm,
    services_for_nodes,
    get_dockyman_base_config,
    get_dockyman_local_config,
    get_context_dir
)


@click.command(help="Clean Docker containers and images.")
@click.argument('target', required=False, default='both')
@click.pass_context
def clean_command(ctx, target):
    """Clean Docker containers and images for 'base' and/or 'local' targets."""
    config_file = ctx.obj.get("config")

    try:
        swarm = get_swarm(config_file)
    except FileNotFoundError:
        click.echo(f"{Fore.RED}[x] Error: Config file not found: {config_file}")
        raise click.Abort()

    _, context_dir = get_context_dir(config_file)
    project_dir = os.path.dirname(os.path.abspath(config_file))
    target_dir = os.path.join(project_dir, context_dir)

    if target in ('base', 'both'):
        click.echo(f"\n{Fore.CYAN}*** Cleaning BASE containers and images ***")
        compose_file, env_file = get_dockyman_base_config(config_file)
        clean_target(swarm, compose_file, env_file, context='base', target_dir='.')

    if target in ('local', 'both'):
        click.echo(f"\n{Fore.CYAN}*** Cleaning LOCAL containers and images ***")
        compose_file = get_dockyman_local_config(config_file)
        env_file = os.path.join(target_dir, '.env')
        clean_target(swarm, compose_file, env_file, context='local', target_dir='.')


def clean_target(swarm, compose_file, base_env_file, context, target_dir):
    """Clean containers and images for a given context (base/local)."""
    try:
        services = services_for_nodes(compose_file, swarm, base_env_file)

        for node, service_names in services.items():
            env_file = base_env_file
            if context == 'local':
                custom_env_file = os.path.join(target_dir, f'.env-{node.id}')
                if os.path.isfile(custom_env_file):
                    env_file = custom_env_file

            click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Cleaning {context.upper()} services {service_names} for node: {Fore.WHITE}{node.id}")
            remove_docker_resources(compose_file, env_file, node, service_names)
    except Exception as e:
        click.echo(f"{Fore.RED}[x] Error during cleanup for {context} context: {e}")

def remove_docker_resources(compose_file, env_file, node, services):
    try:
        docker = DockerClient(
            host=node.docker_daemon_address,
            compose_files=[compose_file],
            compose_env_files=[env_file]
        )

        # Remove containers
        results = docker.compose.rm(services=services, stop=True)
        if results:
            click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Removing stopped containers for services: {services}")
            for log_type, log_message in results:
                msg = log_message[1] if isinstance(log_message, tuple) else log_message
                text = msg.decode().strip()
                if "server: error reading preface from client" in text:
                    continue
                color = Fore.LIGHTBLACK_EX if log_type == "stdout" else Fore.RED
                click.echo(f"\t{color}{text}", err=(log_type == "stderr"))
            click.echo(f"\t{Fore.GREEN} [✓] Containers removed for node {node.id}.")

        # Remove images
        images = [svc.image for svc in docker.compose.config().services.values() if svc.image]
        if images:
            for image in images:
                click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Removing image {image} from node {node.id}")
                docker.image.remove(image, force=True, prune=True)
                click.echo(f"\t{Fore.GREEN} [✓] Image {image} removed successfully!")
        else:
            click.echo(f"\t{Fore.YELLOW} [!] No images found to remove on node {node.id}")

    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Error during cleanup on node {node.id}: {e}")


if __name__ == "__main__":
    clean_command()
