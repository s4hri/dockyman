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
from dockyman.commands.setup import has_nvidia_hardware
from dockyman.config import PREFIX_TARGET, DISPLAY, LOCALHOST_USER
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

# Future work: Consider buildx to build multi-platform images
# https://docs.docker.com/buildx/working-with-buildx/

@click.command(help="Build Docker containers using Docker Compose.")
@click.argument('target', required=False, default='both')
@click.argument('config_file', required=False, default='dockyman.yaml')
def build_command(config_file, target):
    """Build Docker containers using Docker Compose for 'base' and/or 'local' configurations."""

    swarm = None
    try:
        config_filepath = os.path.join(PREFIX_TARGET, config_file)
        swarm = get_swarm(config_filepath)
        extra_env_vars = load_extra_env_vars_from_dockyman(config_filepath)
        compose_base_filepath, env_base_filepath = get_dockyman_base_config(config_filepath)
        compose_local_filepath = get_dockyman_local_config(config_filepath)

    except FileNotFoundError:
        click.echo(f"\n{Fore.RED}[x] Error: Could not load or parse config file: {config_filepath}")
        raise click.Abort()

    if target == 'base' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Building BASE images ***")
        build_base(swarm, compose_base_filepath, env_base_filepath)

    if target == 'local' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Building LOCAL images ***")
        build_local(swarm, compose_local_filepath, env_base_filepath, extra_env_vars)

def build_base(swarm, compose_filepath, env_filepath):
    """Build base containers using Docker Compose."""
    build_docker_base(compose_filepath, env_filepath, swarm)

def build_local(swarm, compose_filepath, env_filepath, extra_env_vars):
    """Build local containers using Docker Compose."""
    build_docker_local(compose_filepath, env_filepath, swarm, extra_env_vars)


def generate_local_env_file_for_node(node, env_file, local_env_file, extra_env_vars=None):
    try:
        click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Generating env file for node: {Fore.WHITE}{node.id}")
        user_uid = run_ssh_command(node.ssh_address, "id -u").strip()
        user_gid = run_ssh_command(node.ssh_address, "id -g").strip()
        xdg_runtime_dir = run_ssh_command(node.ssh_address, "echo $XDG_RUNTIME_DIR").strip()

        env_vars = load_env_variables(env_file)
        env_vars.update(extra_env_vars)

        local_groups = env_vars["LOCAL_IMAGE_GROUPS"].strip()
        group_names = [group.strip() for group in local_groups.split(",") if group.strip()]
        group_ids_list = []

        for group in group_names:
            group_id = run_ssh_command(node.ssh_address, f"getent group {group} | cut -d: -f3").strip()
            if not group_id.isdigit():
                raise ValueError(f"Group '{group}' not found or invalid on node {node.ssh_address}")
            group_ids_list.append(group_id)

        group_ids = ",".join(group_ids_list)

        env_vars.update({
            "USER_UID": user_uid,
            "USER_GID": user_gid,
            "GROUP_IDS": group_ids,
            "XDG_RUNTIME_DIR": xdg_runtime_dir,
            "DISPLAY": DISPLAY,
            "USER": LOCALHOST_USER,
            "GPU_PROFILE": 'nvidia-gpu' if has_nvidia_hardware(node.ssh_address) else 'no-gpu',
        })

        generate_env_file(local_env_file, env_vars)
    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Error generating env file for node {node.id}: {e}")


def build_docker_base(compose_file, env_file, swarm):
    services = services_for_nodes(compose_file, swarm, env_file)
    for target_node, service_names in services.items():
        click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Building BASE services {service_names} defined in the compose file: {Fore.WHITE}{compose_file} (env_file: {env_file})")
        build_docker_compose_service(compose_file, env_file, target_node, service_names)


def build_docker_local(compose_file, base_env_file, swarm, extra_env_vars):
    services = services_for_nodes(compose_file, swarm, base_env_file)
    for target_node, service_names in services.items():
        if target_node == swarm.manager:
            local_env_file = os.path.join(PREFIX_TARGET, '.env')
        else:
            local_env_file = os.path.join(PREFIX_TARGET, '.env-' + target_node.id)
        generate_local_env_file_for_node(target_node, base_env_file, local_env_file, extra_env_vars)
        click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Building LOCAL services {service_names} defined in the compose file: {Fore.WHITE}{compose_file} (env_file: {local_env_file})")
        build_docker_compose_service(compose_file, local_env_file, target_node, service_names)



def build_docker_compose_service(compose_file, env_file, node, services):
    try:
        docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_files=[env_file])

        # Retrieve the Docker Compose project configuration
        project_config = docker.compose.config()
        images = []
        for service_name, service in project_config.services.items():
            if service_name in services:
                images.append(service.image)

        click.echo(f"\n{Fore.LIGHTBLACK_EX} -> Building image(s) {images} in the node: {Fore.WHITE}{node.id}")

        for log_type, log_message in docker.compose.build(services=services, stream_logs=True):
            if isinstance(log_message, tuple):
                log_message = log_message[1]  # Extract the actual message part of the tuple
            if "server: error reading preface from client" in log_message.decode('utf-8'):
                continue  # Filter out the specific error message
            if log_type == "stdout":
                click.echo(f"\t{Fore.LIGHTBLACK_EX} {log_message.decode('utf-8').strip()}")
        click.echo(f"\t{Fore.GREEN} [✓] Docker Image(s) {images} built successfully.")
    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Error builing image(s) {images} process: {e}")

if __name__ == "__main__":
    build_command()
