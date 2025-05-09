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
    get_dockyman_base_config
)


@click.command(help="Push Docker base images for all swarm nodes.")
@click.argument('config_file', required=False, default='dockyman.yaml')
def push_command(config_file):
    """Push Docker base images on manager and worker nodes."""
    try:
        config_path = os.path.join(PREFIX_TARGET, config_file)
        swarm = get_swarm(config_path)
        compose_file, env_file = get_dockyman_base_config(config_path)
    except Exception as e:
        click.echo(f"{Fore.RED}[x] Error loading configuration: {e}")
        raise click.Abort()

    push_images_for_all_nodes(swarm, compose_file, env_file)


def push_images_for_all_nodes(swarm, compose_file, env_file):
    """Push services for all nodes defined in the swarm."""
    services = services_for_nodes(compose_file, swarm, env_file)
    for node, service_names in services.items():
        click.echo(f"{Fore.CYAN}*** Pushing base services {service_names} on node {node.id} ***")
        push_docker_images(compose_file, env_file, node, service_names)


def push_docker_images(compose_file, env_file, node, services=None):
    docker = DockerClient(
        host=node.docker_daemon_address,
        compose_files=[compose_file],
        compose_env_files=[env_file]
    )
    try:
        docker.compose.push(services=services)
        click.echo(f"{Fore.GREEN}[✓] Pushed images successfully on {node.id}.")
    except Exception as e:
        click.echo(f"{Fore.RED}[x] Error pushing images on node {node.id}: {e}")


if __name__ == "__main__":
    push_command()
