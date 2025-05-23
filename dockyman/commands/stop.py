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

from dockyman.utils import (
    get_swarm,
    get_dockyman_runtime_config,
    services_for_nodes,
    services_in_profiles,
    load_env_variables
)
from dockyman.config import PREFIX_TARGET

@click.command(help="Stop and remove Docker containers using Docker Compose.")
@click.argument('config_file', required=False, default='dockyman.yaml')
def stop_command(config_file):
    """Stop and remove Docker Compose services for all swarm nodes."""
    try:
        config_filepath = os.path.join(PREFIX_TARGET, config_file)
        swarm = get_swarm(config_filepath)
        compose_file, env_file = get_dockyman_runtime_config(config_filepath)
    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Error loading config: {e}")
        raise click.Abort()
    
    stop_docker_compose_for_all(swarm, compose_file, env_file)


def stop_docker_compose_for_all(swarm, compose_file, default_env_file):
    """Iterate over all nodes and stop/remove services."""
    try:
        for node in swarm.workers + [swarm.manager]:
            role = "manager" if node == swarm.manager else "worker"
            env_file = os.path.join(PREFIX_TARGET, f'.env-{node.id}') \
                if node != swarm.manager else default_env_file

            if not os.path.isfile(env_file):
                env_file = default_env_file

            # Skip nodes with no services
            services = services_for_nodes(compose_file, swarm, env_file)
            if services and node not in services:
                continue

            click.echo(f"\n{Fore.WHITE}-> Preparing to stop services on {role} node: {Fore.CYAN}{node.id}")
            stop_docker_compose_for_node(compose_file, node, env_file, services[node])

    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Error during stop sequence: {e}")


def stop_docker_compose_for_node(compose_file, node, env_file, services):
    """Stop and remove services for a single node."""
    env_vars = load_env_variables(env_file)
    profiles = env_vars.get("COMPOSE_PROFILES", "").split(",") if "COMPOSE_PROFILES" in env_vars else []

    docker = DockerClient(
        host=node.docker_daemon_address,
        compose_files=[compose_file],
        compose_env_files=[env_file],
        compose_profiles=profiles
    )

    #services = services_in_profiles(compose_file, profiles)
    if services:
        click.echo(f"{Fore.LIGHTBLACK_EX}[.] Stopping services: {services}")

    try:
        docker.compose.stop(services=services or None)
        docker.compose.down(remove_orphans=True)
        click.echo(f"{Fore.GREEN}[✓] Services stopped and removed successfully for node {node.id}.")
    except Exception as e:
        click.echo(f"{Fore.RED}[x] Error stopping services for node {node.id}: {e}")


if __name__ == "__main__":
    stop_command()
