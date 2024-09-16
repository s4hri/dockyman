import click
import os
from python_on_whales import DockerClient
from colorama import Fore
from dockyman.utils import get_swarm, services_for_nodes
from dockyman.config import PREFIX_TARGET

@click.command(help="Stop and remove Docker containers using Docker Compose.")
@click.argument('nodes_file', required=False, default='nodes.yaml')
def stop_command(nodes_file):
    """Stop and remove Docker Compose services for the manager and workers defined in the swarm."""

    swarm = None
    try:
        nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
        swarm = get_swarm(nodes_file_path)
    except FileNotFoundError:
        click.echo(f"{Fore.RED}Error: Nodes configuration file not found.")
        raise click.Abort()

    if not swarm:
        click.echo(f"{Fore.RED}Error: Unable to retrieve swarm configuration.")
        raise click.Abort()

    # Stop and remove docker compose services for manager and workers
    stop_docker_compose_for_all(swarm)


def stop_docker_compose_for_all(swarm):
    """Stop and remove docker compose services for manager and workers using python-on-whales."""
    compose_file = os.path.join(PREFIX_TARGET, "compose.yaml")

    services = services_for_nodes(compose_file, swarm)
    for target_node, service_names in services.items():
        if target_node == swarm.manager:
            local_env_file = os.path.join(PREFIX_TARGET, '.env')
        else:
            local_env_file = os.path.join(PREFIX_TARGET, '.env-' + target_node.id)
        click.echo(f"{Fore.CYAN}*** Stopping services {service_names} on {target_node.id}")
        stop_docker_compose_for_node(target_node, local_env_file, service_names)


def stop_docker_compose_for_node(node, env_file, services=None):
    """Stop and remove Docker Compose services for a specific node."""
    compose_file = os.path.join(PREFIX_TARGET, "compose.yaml")
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file)

    try:
        # Stop and remove the services
        docker.compose.down(services=services, remove_orphans=True, volumes=True)
        click.echo(f"{Fore.GREEN}Services stopped and removed successfully for node {node.id}.")

    except Exception as e:
        click.echo(f"{Fore.RED}Error during stop/remove process for node {node.id}: {e}")


if __name__ == "__main__":
    stop_command()
