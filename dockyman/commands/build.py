import click
import os

from python_on_whales import DockerClient
from colorama import Fore, Style, init
from dockyman.utils import run_ssh_command
from dockyman.commands.setup import has_nvidia_hardware


# Initialize colorama
init(autoreset=True, strip=False, convert=False)

@click.command(help="Build Docker containers using Docker Compose.")
@click.argument('target', required=False, default='both')
@click.argument('host', required=False, default='ssh://localhost')
def build_command(target, host):
    """Build Docker containers using Docker Compose for 'base' and/or 'local' configurations."""
    
    ssh_address = host

    if target == 'base' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Building base containers on {host} ***")
        build_base(ssh_address)

    if target == 'local' or target == 'both':
        click.echo(f"\n{Fore.CYAN}*** Building local containers on {host} ***")
        build_local(ssh_address)

def build_base(host):
    """Build base containers using Docker Compose."""
    compose_file = 'base/compose.yaml'
    env_file = 'dockyman.env'
    build_docker_compose(host, compose_file, env_file)

def build_local(host):
    """Build local containers using Docker Compose."""
    compose_file = 'local/compose.yaml'
    env_file = 'dockyman.env'

    # Get user and group information
    user_uid = run_ssh_command(host, "id -u").strip()
    user_gid = run_ssh_command(host, "id -g").strip()
    local_groups = get_env_variable(env_file, "LOCAL_IMAGE_GROUPS")
    group_ids = ",".join([run_ssh_command(host, f"getent group {group} | cut -d: -f3").strip() for group in local_groups.split(",")])

    # Set environment variables
    os.environ["USER_UID"] = user_uid
    os.environ["USER_GID"] = user_gid
    os.environ["GROUP_IDS"] = group_ids

    # Load all variables from dockyman.env
    env_vars = load_env_variables(env_file)

    # Determine GPU_PROFILE
    if has_nvidia_hardware(host):
        env_vars["GPU_PROFILE"] = 'nvidia-gpu'
    else:
        env_vars["GPU_PROFILE"] = 'no-gpu'

    # Generate the .env file
    generate_env_file('.env', env_vars)
    
    build_docker_compose(host, compose_file, env_file)

    # Unset environment variables
    del os.environ["USER_UID"]
    del os.environ["USER_GID"]
    del os.environ["GROUP_IDS"]

def build_docker_compose(host, compose_file, env_file):
    """Build Docker containers using Docker Compose with specified files and environment variables."""
    click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} build")

    try:
        if host == 'localhost':
            docker = DockerClient(compose_files=[compose_file], compose_env_file=env_file)
        else:
            # Connect to the remote Docker daemon using the host parameter
            docker = DockerClient(host=f"{host}", compose_files=[compose_file], compose_env_file=env_file)

        for log_type, log_message in docker.compose.build(stream_logs=True):
            if isinstance(log_message, tuple):
                log_message = log_message[1]  # Extract the actual message part of the tuple
            if "server: error reading preface from client" in log_message.decode('utf-8'):
                continue  # Filter out the specific error message
            if log_type == "stdout":
                click.echo(f"{Fore.GREEN}{log_message.decode('utf-8').strip()}")
            elif log_type == "stderr":
                click.echo(f"{Fore.RED}{log_message.decode('utf-8').strip()}", err=True)
        click.echo(f"{Fore.GREEN}Build completed successfully for {compose_file}.")
    except Exception as e:
        click.echo(f"{Fore.RED}Error during build process: {e}")
        raise e

def get_env_variable(env_file, variable):
    """Get the value of a specific environment variable from the .env file."""
    with open(env_file, 'r') as file:
        for line in file:
            if line.startswith(variable):
                return line.split('=')[1].strip()
    return None

def load_env_variables(env_file):
    """Load all environment variables from the given .env file."""
    env_vars = {}
    with open(env_file, 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    return env_vars

def generate_env_file(file_path, env_vars):
    """Generate an .env file with the given environment variables."""
    with open(file_path, 'w') as file:
        for key, value in env_vars.items():
            file.write(f"{key}={value}\n")

if __name__ == "__main__":
    build_command()
