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
from dockyman.commands.setup import check_nvidia_hardware
from dockyman.config import DEFAULT_CONFIG_FILE, DISPLAY, PREFIX_TARGET
from dockyman.utils import (
    run_ssh_command,
    get_swarm,
    load_env_variables,
    generate_env_file,
    services_for_nodes,
    get_dockyman_base_config,
    get_dockyman_local_config,
    load_extra_env_vars_from_dockyman
)

@click.command(help="Build Docker containers using Docker Compose.")
@click.argument('target', required=False, default='both')
@click.pass_context
def build_command(ctx, target):
    """Build Docker containers for 'base' and/or 'local' targets."""
    config_file = ctx.obj.get('config', DEFAULT_CONFIG_FILE)

    try:
        swarm = get_swarm(config_file)
        extra_env_vars = load_extra_env_vars_from_dockyman(config_file)
        compose_base, env_base = get_dockyman_base_config(config_file)
        compose_local = get_dockyman_local_config(config_file)
    except FileNotFoundError:
        click.echo(f"\n{Fore.RED}[x] Error: Config file not found: {config_file}")
        raise click.Abort()
    except Exception as e:
        click.echo(f"\n{Fore.RED}[x] Error loading configuration: {e}")
        raise click.Abort()

    if target in ('base', 'both'):
        click.echo(f"\n{Fore.CYAN}*** Building BASE images ***")
        build_base(swarm, compose_base, env_base)

    if target in ('local', 'both'):
        click.echo(f"\n{Fore.CYAN}*** Building LOCAL images ***")
        build_local(swarm, compose_local, env_base, extra_env_vars)

def build_base(swarm, compose_file, env_file):
    services = services_for_nodes(compose_file, swarm, env_file)
    for node, service_names in services.items():
        click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Building BASE services {service_names} on node {node.id}")
        build_docker_compose_service(compose_file, env_file, node, service_names)

def build_local(swarm, compose_file, base_env_file, extra_env_vars):
    services = services_for_nodes(compose_file, swarm, base_env_file)
    for node, service_names in services.items():
        local_env_file = os.path.join(PREFIX_TARGET, f'.env-{node.id}' if node != swarm.manager else '.env')
        generate_local_env_file(node, base_env_file, local_env_file, extra_env_vars)
        click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Building LOCAL services {service_names} on node {node.id}")
        build_docker_compose_service(compose_file, local_env_file, node, service_names)

def generate_local_env_file(node, env_file, output_file, extra_env_vars):
    try:
        click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Generating env file for node: {Fore.WHITE}{node.id}")
        env_vars = load_env_variables(env_file)
        env_vars.update(extra_env_vars or {})
        env_vars.update({
            "USER_UID": run_ssh_command(node.ssh_address, "id -u").strip(),
            "USER_GID": run_ssh_command(node.ssh_address, "id -g").strip(),
            "USER": run_ssh_command(node.ssh_address, "id -un").strip(),
            "XDG_RUNTIME_DIR": run_ssh_command(node.ssh_address, "echo $XDG_RUNTIME_DIR").strip(),
            "GPU_PROFILE": 'nvidia-gpu' if check_nvidia_hardware(node.ssh_address) else 'no-gpu',
            "DISPLAY": DISPLAY
        })

        group_names = [g.strip() for g in env_vars.get("LOCAL_IMAGE_GROUPS", "").split(",") if g.strip()]
        group_ids = ",".join(
            run_ssh_command(node.ssh_address, f"getent group {group} | cut -d: -f3").strip()
            for group in group_names
        )
        env_vars["GROUP_IDS"] = group_ids

        generate_env_file(output_file, env_vars)
    except Exception as e:
        click.echo(f"\t{Fore.RED}[x] Error generating env file for node {node.id}: {e}")

def build_docker_compose_service(compose_file, env_file, node, services):
    try:
        docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_files=[env_file])
        images = [svc.image for svc_name, svc in docker.compose.config().services.items() if svc_name in services]
        click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Building image(s) {images} on node {node.id}")
        for log_type, message in docker.compose.build(services=services, stream_logs=True):
            if isinstance(message, tuple):
                message = message[1]
            if b"server: error reading preface from client" in message:
                continue
            click.echo(f"\t{Fore.LIGHTBLACK_EX}{message.decode().strip()}")
        click.echo(f"\t{Fore.GREEN}[✓] Docker Image(s) {images} built successfully.")
    except Exception as e:
        click.echo(f"\t{Fore.RED}[x] Error building images {services} on node {node.id}: {e}")

if __name__ == "__main__":
    build_command()
