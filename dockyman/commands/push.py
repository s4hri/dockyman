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
from python_on_whales import DockerClient
from colorama import Fore

from dockyman.config import DEFAULT_CONFIG_FILE
from dockyman.utils import (
    get_swarm,
    services_for_nodes,
    get_dockyman_base_config
)


@click.command(help="Push Docker base images for all swarm nodes.")
@click.pass_context
def push_command(ctx):
    """Push Docker base images on manager and worker nodes."""
    config_file = ctx.obj.get('config', DEFAULT_CONFIG_FILE)

    try:
        swarm = get_swarm(config_file)
        compose_file, env_file = get_dockyman_base_config(config_file)

        click.echo(f"{Fore.LIGHTBLACK_EX} -> Loaded configuration from: {config_file}")
        push_images_for_all_nodes(swarm, compose_file, env_file)

    except FileNotFoundError:
        click.echo(f"{Fore.RED}[x] Config file not found: {config_file}")
        raise click.Abort()

    except Exception as e:
        click.echo(f"{Fore.RED}[x] Error: {e}")
        raise click.Abort()


def push_images_for_all_nodes(swarm, compose_file, env_file):
    """Push services for all nodes defined in the swarm."""
    services = services_for_nodes(compose_file, swarm, env_file)

    for node, service_names in services.items():
        click.echo(f"\n{Fore.CYAN}*** Pushing BASE services {service_names} on node {Fore.WHITE}{node.id} ***")
        push_docker_images(compose_file, env_file, node, service_names)


def push_docker_images(compose_file, env_file, node, services=None):
    docker = DockerClient(
        host=node.docker_daemon_address,
        compose_files=[compose_file],
        compose_env_files=[env_file]
    )

    try:
        for log_type, log_message in docker.compose.push(services=services, stream_logs=True):
            if isinstance(log_message, tuple):
                log_message = log_message[1]
            msg = log_message.decode('utf-8').strip()
            if "server: error reading preface from client" in msg:
                continue
            color = Fore.LIGHTBLACK_EX if log_type == "stdout" else Fore.RED
            click.echo(f"\t{color}{msg}", err=(log_type == "stderr"))

        click.echo(f"\t{Fore.GREEN}[✓] Pushed images successfully on {node.id}.")

    except Exception as e:
        click.echo(f"\t{Fore.RED}[x] Error pushing images on {node.id}: {e}")


if __name__ == "__main__":
    push_command()
