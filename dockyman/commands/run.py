import click
import os
from python_on_whales import DockerClient
from colorama import Fore
from dockyman.utils import get_swarm, services_for_nodes, load_env_variables, services_in_profiles
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
        click.echo(f"{Fore.RED}Error: Nodes configuration file not found.")
        raise click.Abort()

    if not swarm:
        click.echo(f"{Fore.RED}Error: Unable to retrieve swarm configuration.")
        raise click.Abort()

    # Run docker compose up for manager and worker nodes
    run_docker_compose_up_for_all(swarm)


def run_docker_compose_up_for_all(swarm):
    """Run docker compose up commands for manager and workers using python-on-whales."""
    compose_file = os.path.join(PREFIX_TARGET, "compose.yaml")

    services = services_for_nodes(compose_file, swarm)
    for target_node, service_names in services.items():
        if target_node == swarm.manager:
            local_env_file = os.path.join(PREFIX_TARGET, '.env')
        else:
            local_env_file = os.path.join(PREFIX_TARGET, '.env-' + target_node.id)
        click.echo(f"{Fore.CYAN}*** Running services {service_names} on {target_node.id}")
        run_docker_compose_for_node(compose_file, target_node, local_env_file, service_names)


def run_docker_compose_for_node(compose_file, node, env_file, services=None):
    """Run Docker Compose action (up or down) for a specific node."""

    env_vars = load_env_variables(env_file)
    if "COMPOSE_PROFILES" in env_vars.keys():
        profiles = env_vars["COMPOSE_PROFILES"].split(',')
    if not profiles:
        profiles = []

    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file, compose_profiles=profiles)
    services = services_in_profiles(compose_file, services, profiles)
    if services:
        click.echo(f"Running services: {services}")
    try:
        docker.compose.up(services=services, detach=False, remove_orphans=True)
        #for service in services:
        #    docker.compose.run(service=service, detach=True, remove=True, tty=False)
        click.echo(f"{Fore.GREEN}Services started successfully for node {node.id}.")
    except Exception as e:
        click.echo(f"{Fore.RED}Error during running process for node {node.id}: {e}")

if __name__ == "__main__":
    run_command()
