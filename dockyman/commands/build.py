import click
from python_on_whales import DockerClient
from dockyman.utils import load_hosts_config, run_ssh_command

@click.command(help="Builds the services on the relative hosts as defined in the compose file.")
@click.argument('compose_file', default='docker-compose.yml')
def build_command(compose_file):
    """Builds the services on the relative hosts as defined in the compose file."""
    docker = DockerClient()
    compose_config = docker.compose.config([compose_file])
    hosts_config = load_hosts_config('hosts.yml')

    for service_name, service in compose_config['services'].items():
        build_context = service['build']['context']
        image_name = service['image']
        placement_constraints = service['deploy']['placement']['constraints']
        
        for constraint in placement_constraints:
            if 'node.hostname' in constraint:
                host = constraint.split('==')[1].strip()
                docker_host = hosts_config['hosts'][host]['ssh']
                click.echo(f'Building {image_name} on {host}...')
                build_and_push_image(docker_host, build_context, image_name)
                click.echo(f'Built {image_name} on {host}')

def build_and_push_image(docker_host, path, image_name):
    docker = DockerClient(host=docker_host)
    # Build the Docker image
    docker.build(path, tags=[image_name])
    # Push the Docker image
    docker.push(image_name)
