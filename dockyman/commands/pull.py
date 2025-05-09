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


@click.command(help="Pull Docker base images for swarm nodes.")
@click.argument('config_file', required=False, default='dockyman.yaml')
def pull_command(config_file):
    """Pull Docker base images on manager and worker nodes."""

    try:
        config_path = os.path.join(PREFIX_TARGET, config_file)
        swarm = get_swarm(config_path)
        compose_file, env_file = get_dockyman_base_config(config_path)
    except Exception as e:
        click.echo(f"{Fore.RED}[x] Error loading configuration: {e}")
        raise click.Abort()

    pull_images_for_all_nodes(swarm, compose_file, env_file)


def pull_images_for_all_nodes(swarm, compose_file, env_file):
    """Pull services for all nodes defined in the swarm."""
    services = services_for_nodes(compose_file, swarm, env_file)
    for node, service_names in services.items():
        click.echo(f"{Fore.CYAN}*** Pulling base services {service_names} on node {node.id} ***")
        pull_docker_images(compose_file, env_file, node, service_names)


def pull_docker_images(compose_file, env_file, node, services=None):
    docker = DockerClient(
        host=node.docker_daemon_address,
        compose_files=[compose_file],
        compose_env_files=[env_file]
    )
    try:
        docker.compose.pull(services=services)
        click.echo(f"{Fore.GREEN}[✓] Pulled images successfully on {node.id}.")
    except Exception as e:
        click.echo(f"{Fore.RED}[x] Error pulling images on node {node.id}: {e}")


if __name__ == "__main__":
    pull_command()
