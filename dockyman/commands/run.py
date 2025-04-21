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
def run_command(nodes_file):
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
    
    # Run docker compose up for manager and worker nodes
    run_docker_compose_up_for_all(swarm)

def run_docker_compose_up_for_all(swarm):
    """Run docker compose up commands for manager and workers using python-on-whales."""
    compose_file = os.path.join(PREFIX_TARGET, "compose.yaml")

    services = services_for_nodes(compose_file, swarm)

    try:
        for target_node, service_names in services.items():
            if target_node != swarm.manager:
                local_env_file = os.path.join(PREFIX_TARGET, '.env-' + target_node.id)
                if not os.path.isfile(local_env_file):
                    local_env_file = os.path.join(PREFIX_TARGET, '.env')
                click.echo(f"\t{Fore.CYAN} [.] Preparing services {service_names} defined to run in the node: {Fore.WHITE}{target_node.id}")
                run_docker_compose_for_node(compose_file, target_node, local_env_file, service_names, detach=True)

        for target_node, service_names in services.items():
            if target_node == swarm.manager:
                local_env_file = os.path.join(PREFIX_TARGET, '.env')
                click.echo(f"\t{Fore.CYAN} [.] Preparing services {service_names} defined to run in the node: {Fore.WHITE}{target_node.id}")
                run_docker_compose_for_node(compose_file, target_node, local_env_file, service_names, detach=True)

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

def run_docker_compose_for_node(compose_file, node, env_file, services=None, detach=False):
    """Run Docker Compose action (up or down) for a specific node."""

    profiles = get_docker_profiles(env_file)
    click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Docker profiles: {profiles}")

    services = services_in_profiles(compose_file, services, profiles)
    click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Running services: {services}")

    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_files=[env_file], compose_profiles=profiles)

    for service in services:
        try:
            click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Starting service {service} in the node: {node.id}...")
            container = docker.compose.run(service, detach=detach, tty=False)
            container_name = container.name if hasattr(container, "name") else None

            # Check if DOCKER_LOGS defined in the .env file is true or false
            
            env_vars = load_env_variables(env_file)
            docker_logs = env_vars.get("DOCKER_LOGS", "false").lower() == "true"
            if container_name:
                if docker_logs:
                    click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] DOCKER_LOGS is set to true in the .env file, streaming logs for service {service}...")
                    if container_name:
                        logs_dir = os.path.join(PREFIX_TARGET, "logs")
                        os.makedirs(logs_dir, exist_ok=True)
                        log_file_path = os.path.join(logs_dir, f"{node.id}_{service}.log")
                        click.echo(f"\t{Fore.LIGHTBLACK_EX} [.] Logging to {Fore.WHITE}{log_file_path}")
                        
                        t = threading.Thread(target=stream_logs, args=(container_name, log_file_path, docker))
                        t.daemon = True
                        t.start()
            else:
                click.echo(f"\t{Fore.YELLOW} [!] Warning: Could not determine container name for service {service}")

        except Exception as e:
            click.echo(f"\t{Fore.RED} [x] Error starting service {service}: {e}")
            raise

    click.echo(f"\t{Fore.GREEN} [✓] Services started successfully in the node: {Fore.WHITE}{node.id}.")


if __name__ == "__main__":
    run_command()
