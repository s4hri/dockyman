import click
import os

from python_on_whales import DockerClient
from colorama import Fore
from dockyman.utils import run_ssh_command, get_swarm, load_env_variables, generate_env_file, get_nodes_for_services
from dockyman.commands.setup import has_nvidia_hardware
from dockyman.config import LOCALHOST_USER, PREFIX_TARGET


# Future work: Consider buildx to build multi-platform images
# https://docs.docker.com/buildx/working-with-buildx/

@click.command(help="Build Docker containers using Docker Compose.")
@click.argument('target', required=False, default='both')
@click.argument('nodes_file', required=False, default='nodes.yaml')
def build_command(target, nodes_file):
    """Build Docker containers using Docker Compose for 'base' and/or 'local' configurations."""

    os.environ['LOCALHOST_USER'] = LOCALHOST_USER

    swarm = None
    try:
        nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
        swarm = get_swarm(nodes_file_path)
    except FileNotFoundError:
        click.echo(f"{Fore.RED}Error: Nodes configuration file not found.")
        raise click.Abort()

    if target == 'base' or target == 'both':
        build_base(swarm)

    if target == 'local' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Building local containers ***")
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
    #try:
    if True:
        click.echo(f"\n{Fore.CYAN}*** Generating env file for node: {node.id}***")
        user_uid = run_ssh_command(node.ssh_address, "id -u").strip()
        user_gid = run_ssh_command(node.ssh_address, "id -g").strip()

        # Load all variables from dockyman.env
        env_vars = load_env_variables(env_file)

        local_groups = env_vars["LOCAL_IMAGE_GROUPS"]
        group_ids = ",".join([run_ssh_command(node.ssh_address, f"getent group {group} | cut -d: -f3").strip() for group in local_groups.split(",")])
                
        env_vars["USER_UID"] = user_uid
        env_vars["USER_GID"] = user_gid
        env_vars["GROUP_IDS"] = group_ids
        generate_env_file(local_env_file, env_vars)
    #except Exception as e:
    #    click.echo(f"{Fore.RED}Error generating env file for service for node {node.id} process: {e}")
    


def build_docker_local(compose_file, swarm, env_file):

    # click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} build")

    # services = get_nodes_for_services(compose_file, swarm)

    # for service, nodes in services.items():
    #     for node in nodes:
    #         try:
    #             click.echo(f"\n{Fore.CYAN}*** Generating env file for local service {service} in node: {node.id}***")
    #             user_uid = run_ssh_command(node.ssh_address, "id -u").strip()
    #             user_gid = run_ssh_command(node.ssh_address, "id -g").strip()

    #             # Load all variables from dockyman.env
    #             env_vars = load_env_variables(env_file)

    #             local_groups = env_vars["LOCAL_IMAGE_GROUPS"]
    #             group_ids = ",".join([run_ssh_command(node.ssh_address, f"getent group {group} | cut -d: -f3").strip() for group in local_groups.split(",")])
                
    #             env_vars["USER_UID"] = user_uid
    #             env_vars["USER_GID"] = user_gid
    #             env_vars["GROUP_IDS"] = group_ids
    #             local_env_file = os.path.join(PREFIX_TARGET, '.env')
    #             generate_env_file(local_env_file, env_vars)
                
    #         except Exception as e:
    #             click.echo(f"{Fore.RED}Error generating env file for service {service} in node {node.id} process: {e}")

    #         build_docker_compose_service(compose_file, local_env_file, service, node)

    #         if os.path.exists(local_env_file):
    #             os.remove(local_env_file)

    local_env_file = os.path.join(PREFIX_TARGET, '.env')
    generate_local_env_file_for_node(swarm.manager, env_file, local_env_file)
    click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {local_env_file} --profile {swarm.manager.id} build")
    build_docker_compose_service(compose_file, local_env_file, swarm.manager.id, swarm.manager)

    for worker in swarm.workers:
        generate_local_env_file_for_node(worker, env_file, local_env_file)
        click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {local_env_file} --profile {worker.id} build")
        build_docker_compose_service(compose_file, local_env_file, worker.id, worker)

    click.echo(f"\n{Fore.CYAN}*** Generating env file for local image in node: {swarm.manager.id}***")
    # Load all variables from dockyman.env
    env_vars = load_env_variables(env_file)
    # Determine GPU_PROFILE
    if has_nvidia_hardware(swarm.manager.ssh_address):
        env_vars["GPU_PROFILE"] = 'nvidia-gpu'
    else:
        env_vars["GPU_PROFILE"] = 'no-gpu'
    generate_env_file(local_env_file, env_vars)


def build_docker_base(compose_file, env_file, swarm):
    """Build Docker containers using Docker Compose with specified files, environment variables and profiles."""
    click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} --profile {swarm.manager.id} build")

    build_docker_compose_service(compose_file, env_file, swarm.manager.id, swarm.manager)

    for worker in swarm.workers:
        click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} --profile {worker.id} build")
        build_docker_compose_service(compose_file, env_file, worker.id, worker)

def build_docker_compose_service(compose_file, env_file, profile, node):
    try:
        docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file, compose_profiles=[profile])

        # Retrieve the Docker Compose project configuration
        project_config = docker.compose.config()
        images = []
        for service_name, service in project_config.services.items():
            images.append(service.image)

        click.echo(f"\n{Fore.CYAN}*** Building image(s) {images} in node: {node.id}***")

        for log_type, log_message in docker.compose.build(stream_logs=True):
            if isinstance(log_message, tuple):
                log_message = log_message[1]  # Extract the actual message part of the tuple
            if "server: error reading preface from client" in log_message.decode('utf-8'):
                continue  # Filter out the specific error message
            if log_type == "stdout":
                click.echo(f"{Fore.LIGHTBLACK_EX}{log_message.decode('utf-8').strip()}")
            elif log_type == "stderr":
                click.echo(f"{Fore.RED}{log_message.decode('utf-8').strip()}", err=True)
        click.echo(f"{Fore.GREEN}Docker Image(s) {images} built successfully.")
    except Exception as e:
        click.echo(f"{Fore.RED}Error builing image(s) {images} process: {e}")

if __name__ == "__main__":
    build_command()
