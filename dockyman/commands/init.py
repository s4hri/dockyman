import click
from dockyman.utils import copy_model

@click.command()
@click.argument('target_directory')
def init_command(target_directory):
    """Copies a set of template files to a target directory."""
    copy_model(target_directory)
    click.echo(f'Templates copied to {target_directory}')
