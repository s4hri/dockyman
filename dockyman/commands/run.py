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
import threading
import click
from python_on_whales import DockerClient
from colorama import Fore

from dockyman.utils import (
    get_swarm,
    services_for_nodes,
    get_docker_profiles,
    load_env_variables,
    get_dockyman_runtime_config,
)
from dockyman.commands.stop import stop_docker_compose_for_all
from dockyman.config import PREFIX_TARGET


@click.command(help="Run Docker containers using Docker Compose.")
@click.argument('config_file', required=False, default='dockyman.yaml')
@click.option('--no_detach', is_flag=True, default=False, help='Run containers in the foreground.')
def run_command(config_file, no_detach):
    """Run Docker Compose services for manager and workers defined in the swarm."""
    try:
        config_path = os.path.join(PREFIX_TARGET, config_file)
        swarm = get_swarm(config_path)
        compose_file, env_file = get_dockyman_runtime_config(config_path)
    except Exception as e:
        click.echo(f"{Fore.RED}[x] Error loading config: {e}")
        raise click.Abort()

    detach = not no_detach
    run_services_for_all_nodes(swarm, compose_file, env_file, detach)


def run_services_for_all_nodes(swarm, compose_file, default_env_file, detach):
    try:
        for node in swarm.workers + [swarm.manager]:
            local_env_file = os.path.join(PREFIX_TARGET, f'.env-{node.id}') if node != swarm.manager else default_env_file
            if not os.path.isfile(local_env_file):
                local_env_file = default_env_file

            services = services_for_nodes(compose_file, swarm, local_env_file)
            if node in services:
                click.echo(f"{Fore.WHITE} -> Running services on node: {Fore.CYAN}{node.id}")
                run_services_for_node(compose_file, node, local_env_file, services[node], detach)

        if detach:
            click.echo(f"{Fore.WHITE} -> Services are running in detached mode.")
            click.echo(f"\t{Fore.YELLOW}Press Enter to stop all services...")
            click.get_text_stream('stdout').flush()
            click.get_text_stream('stdin').readline()
            stop_docker_compose_for_all(swarm, compose_file, default_env_file)

    except Exception as e:
        click.echo(f"{Fore.RED}[x] Error running services: {e}")


def run_services_for_node(compose_file, node, env_file, services, detach=False):
    profiles = get_docker_profiles(env_file)
    click.echo(f"{Fore.LIGHTBLACK_EX} [.] Docker profiles: {profiles}")
    click.echo(f"{Fore.LIGHTBLACK_EX} [.] Services to run: {services}")

    docker = DockerClient(
        host=node.docker_daemon_address,
        compose_files=[compose_file],
        compose_env_files=[env_file],
        compose_profiles=profiles
    )

    try:
        docker.compose.up(services, detach=detach, remove_orphans=True)
        if detach:
            click.echo(f"{Fore.GREEN} [✓] Services started for node {node.id}.")
            if should_stream_logs(env_file):
                stream_logs_for_node(docker, node)
    except Exception as e:
        click.echo(f"{Fore.RED} [x] Error running on node {node.id}: {e}")


def should_stream_logs(env_file):
    env_vars = load_env_variables(env_file)
    return env_vars.get("DOCKER_LOGS", "false").lower() == "true"


def stream_logs_for_node(docker, node):
    logs_dir = os.path.join(PREFIX_TARGET, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    for container in docker.compose.ps():
        log_path = os.path.join(logs_dir, f"{node.id}_{container.name}.log")
        click.echo(f"{Fore.LIGHTBLACK_EX} [.] Logging to {Fore.WHITE}{log_path}")
        t = threading.Thread(target=stream_logs, args=(container.name, log_path, docker))
        t.daemon = True
        t.start()


def stream_logs(container_name, log_file_path, docker):
    with open(log_file_path, "w") as log_file:
        for log in docker.container.logs(container_name, follow=True, stream=True):
            content = log[1] if isinstance(log, tuple) else log
            log_file.write(content.decode('utf-8'))
            log_file.flush()


if __name__ == "__main__":
    run_command()
