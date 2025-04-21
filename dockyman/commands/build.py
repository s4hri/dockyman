import click
import os

from python_on_whales import DockerClient
from colorama import Fore
from dockyman.utils import run_ssh_command, get_swarm, load_env_variables, generate_env_file, get_docker_profiles, services_for_nodes
from dockyman.commands.setup import has_nvidia_hardware
from dockyman.config import PREFIX_TARGET, DISPLAY


# Future work: Consider buildx to build multi-platform images
# https://docs.docker.com/buildx/working-with-buildx/

@click.command(help="Build Docker containers using Docker Compose.")
@click.argument('target', required=False, default='both')
@click.argument('nodes_file', required=False, default='nodes.yaml')
def build_command(target, nodes_file):
    """Build Docker containers using Docker Compose for 'base' and/or 'local' configurations."""

    swarm = None
    try:
        nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
        swarm = get_swarm(nodes_file_path)
    except FileNotFoundError:
        click.echo(f"\n{Fore.RED}Error: Nodes configuration file not found.")
        raise click.Abort()

    if target == 'base' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Building BASE images ***")
        build_base(swarm)

    if target == 'local' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Building LOCAL images ***")
        build_local(swarm)

def build_base(swarm):
    """Build base containers using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'base/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')
    build_docker_base(compose_file, env_file, swarm)

def build_local(swarm):
    """Build local containers using Docker Compose."""
    compose_file = os.path.join(PREFIX_TARGET, 'local/compose.yaml')
    env_file = os.path.join(PREFIX_TARGET, 'dockyman.env')
    build_docker_local(compose_file, swarm, env_file)


def generate_local_env_file_for_node(node, env_file, local_env_file):
    try:
        click.echo(f"\t{Fore.CYAN} [.] Generating env file for node: {node.id}***")
        user_uid = run_ssh_command(node.ssh_address, "id -u").strip()
        user_gid = run_ssh_command(node.ssh_address, "id -g").strip()
        xdg_runtime_dir = run_ssh_command(node.ssh_address, "echo $XDG_RUNTIME_DIR").strip()

        # Load all variables from dockyman.env
        env_vars = load_env_variables(env_file)

        local_groups = env_vars["LOCAL_IMAGE_GROUPS"].strip()
        group_names = [group.strip() for group in local_groups.split(",") if group.strip()]
        group_ids_list = []

        for group in group_names:
            group_id = run_ssh_command(node.ssh_address, f"getent group {group} | cut -d: -f3").strip()
            if not group_id.isdigit():
                raise ValueError(f"Group '{group}' not found or invalid on node {node.ssh_address}")
            group_ids_list.append(group_id)

        group_ids = ",".join(group_ids_list)
                
        env_vars["USER_UID"] = user_uid
        env_vars["USER_GID"] = user_gid
        env_vars["GROUP_IDS"] = group_ids
        env_vars["XDG_RUNTIME_DIR"] = xdg_runtime_dir
        env_vars["DISPLAY"] = DISPLAY

        # Determine GPU_PROFILE
        if has_nvidia_hardware(node.ssh_address):
            env_vars["GPU_PROFILE"] = 'nvidia-gpu'
        else:
            env_vars["GPU_PROFILE"] = 'no-gpu'
        generate_env_file(local_env_file, env_vars)
    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Error generating env file for service for node {node.id} process: {e}")

def build_docker_base(compose_file, env_file, swarm):
    services = services_for_nodes(compose_file, swarm, env_file)
    for target_node, service_names in services.items():
        click.echo(f"\t{Fore.CYAN} [.] Building BASE services {service_names} defined in the compose file: {Fore.WHITE}{compose_file}")
        build_docker_compose_service(compose_file, env_file, target_node, service_names)


def build_docker_local(compose_file, swarm, env_file):
    services = services_for_nodes(compose_file, swarm, env_file)
    for target_node, service_names in services.items():
        if target_node == swarm.manager:
            local_env_file = os.path.join(PREFIX_TARGET, '.env')
        else:
            local_env_file = os.path.join(PREFIX_TARGET, '.env-' + target_node.id)
        generate_local_env_file_for_node(target_node, env_file, local_env_file)
        click.echo(f"\t{Fore.CYAN} [.] Building LOCAL services {service_names} defined in the compose file: {Fore.WHITE}{compose_file}")
        build_docker_compose_service(compose_file, local_env_file, target_node, service_names)



def build_docker_compose_service(compose_file, env_file, node, services=None):
    try:
        docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_files=[env_file])

        # Retrieve the Docker Compose project configuration
        project_config = docker.compose.config()
        images = []
        for service_name, service in project_config.services.items():
            images.append(service.image)

        click.echo(f"\t{Fore.CYAN} [.] Building image(s) {images} in the node: {Fore.WHITE}{node.id}")

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
