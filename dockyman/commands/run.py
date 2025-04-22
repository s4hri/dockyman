import click
import os
import threading
from python_on_whales import DockerClient
from colorama import Fore
from dockyman.utils import get_swarm, services_for_nodes, services_in_profiles, get_docker_profiles, load_env_variables
from dockyman.commands.stop import stop_docker_compose_for_all
from dockyman.config import PREFIX_TARGET

@click.command(help="Run Docker containers using Docker Compose.")
@click.argument('nodes_file', required=False, default='nodes.yaml')
@click.option('--no_detach', is_flag=True, default=False, help='Run containers in detached mode.')
def run_command(nodes_file, no_detach):
    """Run Docker Compose services for the manager and workers defined in the swarm."""

    swarm = None
    try:
        nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
        swarm = get_swarm(nodes_file_path)
    except FileNotFoundError:
        click.echo(f"\t{Fore.RED} [x] Error: Nodes configuration file not found.")
        raise click.Abort()

    if not swarm:
        click.echo(f"\t{Fore.RED} [x] Error: Unable to retrieve swarm configuration.")
        raise click.Abort()

    detach = not no_detach
    # Run docker compose up for manager and worker nodes
    run_docker_compose_up_for_all(swarm, detach)

def run_docker_compose_up_for_all(swarm, detach):
    """Run docker compose up commands for manager and workers using python-on-whales."""
    compose_file = os.path.join(PREFIX_TARGET, "compose.yaml")

    services = services_for_nodes(compose_file, swarm)

    try:
        for worker in swarm.workers:
            local_env_file = os.path.join(PREFIX_TARGET, '.env-' + worker.id)
            if not os.path.isfile(local_env_file):
                local_env_file = os.path.join(PREFIX_TARGET, '.env')
            click.echo(f"\n{Fore.WHITE} -> Preparing services to run in the worker node: {Fore.CYAN}{worker.id}")
            run_docker_compose_for_node(compose_file, worker, local_env_file, detach=detach)

        manager = swarm.manager
        local_env_file = os.path.join(PREFIX_TARGET, '.env')
        click.echo(f"\n{Fore.WHITE} -> Preparing services to run in the manager node: {Fore.CYAN}{manager.id}")
        run_docker_compose_for_node(compose_file, manager, local_env_file, detach=detach)

        if detach:
            click.echo(f"\n{Fore.WHITE} -> Running containers from in detached mode...")
            click.echo(f"\n\t{Fore.RED} [!] Press Enter to stop all services ...")
            click.get_text_stream('stdout').flush()
            click.get_text_stream('stdin').readline()

        stop_docker_compose_for_all(swarm)

    except Exception as e:
        click.echo(f"\t{Fore.RED} [x] Error during running the services: {e}")


def stream_logs(container_name, log_file_path, docker):
    """Stream logs from a container into a file."""
    with open(log_file_path, "w") as log_file:
        for log in docker.container.logs(container_name, follow=True, stream=True):
            if log:
                # Check if the log is a tuple (stream_type, stream_content)
                if isinstance(log, tuple):
                    stream_type, stream_content = log
                    log_file.write(stream_content.decode('utf-8'))
                    log_file.flush()
                else:
                    # If not a tuple, just write the content
                    log_file.write(log.decode('utf-8'))
                    log_file.flush()

def run_docker_compose_for_node(compose_file, node, env_file, detach=False):
    """Run Docker Compose action (up or down) for a specific node."""

    profiles = get_docker_profiles(env_file)
    click.echo(f"{Fore.LIGHTBLACK_EX} [.] Docker profiles: {profiles}")

    services = services_in_profiles(compose_file, profiles)
    click.echo(f"{Fore.LIGHTBLACK_EX} [.] Running services: {services}")

    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_files=[env_file], compose_profiles=profiles)
    try:
        docker.compose.up(detach=detach, remove_orphans=True)

        if detach:
            click.echo(f"{Fore.GREEN} [✓] Services started successfully for node {node.id}.")

            # Check if DOCKER_LOGS defined in the .env file is true or false
            env_vars = load_env_variables(env_file)
            docker_logs = env_vars.get("DOCKER_LOGS", "false").lower() == "true"
            if docker_logs:
                click.echo(f"{Fore.LIGHTBLACK_EX} [.] DOCKER_LOGS is set to true in the .env file, streaming logs for services {services}...")
                for container in docker.compose.ps():
                    logs_dir = os.path.join(PREFIX_TARGET, "logs")
                    os.makedirs(logs_dir, exist_ok=True)
                    log_file_path = os.path.join(logs_dir, f"{node.id}_{container.name}.log")
                    click.echo(f"{Fore.LIGHTBLACK_EX} [.] Logging to {Fore.WHITE}{log_file_path}")

                    t = threading.Thread(target=stream_logs, args=(container.name, log_file_path, docker))
                    t.daemon = True
                    t.start()

    except Exception as e:
        click.echo(f"{Fore.RED} [x] Error during running process for node {node.id}: {e}")

if __name__ == "__main__":
    run_command()
