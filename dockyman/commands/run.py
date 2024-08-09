import click
from python_on_whales import DockerClient
from colorama import Fore, Style, init
import os
import signal
import sys

# Initialize colorama
init(autoreset=True, strip=False, convert=False)

def signal_handler(signal, frame):
    """Handle the user interruption and run docker-compose down."""
    click.echo(f"{Fore.RED}\nUser interrupted. Stopping all containers...")
    try:
        docker.compose.down()
        click.echo(f"{Fore.GREEN}All containers stopped successfully.")
    except Exception as e:
        click.echo(f"{Fore.RED}Error during stopping containers: {e}")
    sys.exit(0)

@click.command(help="Run Docker containers using Docker Compose.")
@click.argument('host', required=False, default='ssh://localhost')
def run_command(host):
    """Run Docker containers using Docker Compose with specified files and environment variables."""
    compose_file = 'compose.yaml'
    env_file = '.env'
    
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    click.echo(f"\n{Fore.CYAN}*** Running containers on {host} ***")
    run_docker_compose(host, compose_file, env_file)

def run_docker_compose(host, compose_file='compose.yaml', env_file='.env'):
    """Run Docker containers using Docker Compose with specified files and environment variables."""

    click.echo(f"{Fore.LIGHTBLACK_EX}Running: docker compose -f {compose_file} --env-file {env_file} up")

    try:
        global docker
        if host == 'localhost':
            docker = DockerClient(compose_files=[compose_file], compose_env_file=env_file)
        else:
            # Connect to the remote Docker daemon using the host parameter
            docker = DockerClient(host=f"{host}", compose_files=[compose_file], compose_env_file=env_file)

        for log_type, log_message in docker.compose.up(detach=False, stream_logs=True):
            if isinstance(log_message, tuple):
                log_message = log_message[1]  # Extract the actual message part of the tuple
            if "server: error reading preface from client" in log_message.decode('utf-8'):
                continue  # Filter out the specific error message
            if log_type == "stdout":
                click.echo(f"{Fore.GREEN}{log_message.decode('utf-8').strip()}")
            elif log_type == "stderr":
                click.echo(f"{Fore.RED}{log_message.decode('utf-8').strip()}", err=True)
        click.echo(f"{Fore.GREEN}Run completed successfully for {compose_file}.")
    except Exception as e:
        click.echo(f"{Fore.RED}Error during run process: {e}")
        raise e

if __name__ == "__main__":
    run_command()
