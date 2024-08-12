import click
import os
from python_on_whales import DockerClient, docker
from colorama import Fore, Style, init
from dockyman.config import PREFIX_TARGET
from dockyman.utils import get_swarm, get_nodes_for_services

@click.command(help="Run Docker containers using Docker Compose.")
@click.argument('nodes_file', required=False, default='nodes.yaml')
def run_command(nodes_file):
    """Run Docker containers using Docker Compose with specified files and environment variables."""
    compose_file = os.path.join(PREFIX_TARGET, 'compose.yaml')
    nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)

    swarm = get_swarm(nodes_file_path)

    #deploy_application_per_node(swarm, compose_file)


    initialize_docker_swarm(swarm)
    #deploy_application_per_node_swarm(swarm, compose_file)
    #destroy_swarm(swarm)

    #deploy_application_per_node(swarm, compose_file)

    #click.echo(f"\n{Fore.CYAN}*** Running containers on {host} ***")



def initialize_docker_swarm(swarm):
    """Initialize Docker Swarm using nodes configuration from a YAML file."""

    manager_node = swarm.manager
    worker_nodes = swarm.workers

    # Use the default Docker Swarm port 2377
    swarm_port = 2377

    # Initialize Docker Swarm on the manager node
    try:
        docker.swarm.init(
            advertise_address=f"{manager_node.host}:{swarm_port}",
            listen_address=f"{manager_node.host}:{swarm_port}",
            availability="active"
        )
        print(f"Swarm initialized on manager node {manager_node.id} successfully.")
    except Exception as e:
        print(f"Error initializing Docker Swarm on manager node: {e}")
        return

    # Check if there are worker nodes
    if not worker_nodes:
        print("No worker nodes defined. Swarm initialized with only the manager node.")
        return

    # Retrieve the manager node's join token for workers
    try:
        worker_join_token = docker.swarm.join_token("worker")
        print("Worker join token retrieved successfully.")
    except Exception as e:
        print(f"Error retrieving worker join token: {e}")
        return

    # Join each worker node to the swarm
    for worker in worker_nodes:
        try:
            worker_docker = DockerClient(host=worker.docker_daemon_address)
            worker_docker.swarm.join(
                manager_address=f"{manager_node.host}:{swarm_port}",
                token=worker_join_token,
                advertise_address=f"{worker.host}:{swarm_port}",
                listen_address=f"{worker.host}:{swarm_port}",
                availability="active"
            )
            print(f"Worker node {worker.host} joined the swarm successfully.")
        except Exception as e:
            print(f"Error joining worker node {worker.host} to the swarm: {e}")

    print("Docker Swarm initialized successfully with manager and worker nodes!")


def destroy_swarm(swarm):
    """Destroy the Docker Swarm by having all nodes leave the swarm."""
    try:
        # Make the manager node leave the swarm
        docker.swarm.leave(force=True)
        print(f"Manager node {swarm.manager.host} left the swarm successfully.")
    except Exception as e:
        print(f"Error leaving swarm on manager node {swarm.manager.host}: {e}")

    # Make each worker node leave the swarm
    for worker in swarm.workers:
        try:
            worker_docker = DockerClient(host=f"ssh://{worker.user}@{worker.host}")
            worker_docker.swarm.leave(force=True)
            print(f"Worker node {worker.host} left the swarm successfully.")
        except Exception as e:
            print(f"Error leaving swarm on worker node {worker.host}: {e}")

    print("Swarm destroyed successfully.")

def deploy_application_per_node_swarm(swarm, compose_file):
    """Deploys the application one node at a time using Swarm with specific environment files."""
    
    try:
        # Connect to the manager node via Docker
        #docker_client = DockerClient(host=f"ssh://{node.user}@{node.host}")
        docker_client = DockerClient()
        env_file = os.path.join(PREFIX_TARGET, '.env')

        # Deploy the stack with node-specific placement constraints
        stack_name = f"stack_on_{swarm.manager.host.replace('.', '_')}"
        docker_client.stack.deploy(
                compose_files=[compose_file],
                name=stack_name,
                env_files=[env_file],
                with_registry_auth=False,
                prune=False
        )
        
    except Exception as e:
        print(f"Error deploying application: {e}")

def deploy_application_per_node(swarm, compose_file):
    """Deploys the application one node at a time."""

    worker_nodes = swarm.workers
    manager_node = swarm.manager

    services = get_nodes_for_services(compose_file, swarm)

    for service, nodes in services.items():
        for node in nodes:
            try:
                # Connect to the node via Docker
                docker_client = DockerClient(host=node.docker_daemon_address, compose_files=[compose_file])

                # Deploy the stack on the node using the node-specific environment file
                docker_client.compose.run(service, detach=True, tty=False)
                print(f"Service {service} executed successfully on node {node.id}")
            
            except Exception as e:
                print(f"Error deploying application on node {node.id}: {e}")

if __name__ == "__main__":
    run_command()
