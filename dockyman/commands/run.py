import click
import os
from python_on_whales import DockerClient
from colorama import Fore
from dockyman.utils import get_swarm, load_compose_file
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
    docker_compose_command = "docker compose"
    compose_file = os.path.join(PREFIX_TARGET, "compose.yaml")

    services = load_compose_file(compose_file).get('services', {})
    for service_name, service_data in services.items():
        target_node = swarm.manager
        local_env_file = os.path.join(PREFIX_TARGET, '.env')
        labels = service_data.get('labels', {})
        node_label = labels.get('dockyman.node')
        if node_label:
            node = swarm.get_node_from_id(node_id=node_label)
            if node:
                if node != swarm.manager:
                    target_node = node
                    local_env_file = os.path.join(PREFIX_TARGET, '.env-' + target_node.id)
        
        click.echo(f"{Fore.LIGHTBLACK_EX}Running on {target_node.id}: docker compose -f {compose_file} --env-file {local_env_file} build ")
        run_docker_compose_for_node(target_node, docker_compose_command, "up", env_file=local_env_file)

def run_docker_compose_for_node(node, docker_compose_command, action, env_file):
    """Run Docker Compose action (up or down) for a specific node."""
    compose_file = os.path.join(PREFIX_TARGET, "compose.yaml")
    docker = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file], compose_env_file=env_file, compose_profiles=[node.id])

    try:
        if action == "up":
            docker.compose.up(detach=True)
            click.echo(f"{Fore.GREEN}Service started successfully for node {node.id}.")
        else:
            click.echo(f"{Fore.RED}Unknown action: {action}")

    except Exception as e:
        click.echo(f"{Fore.RED}Error during {action} process for node {node.id}: {e}")

if __name__ == "__main__":
    run_command()
