import click
import os
import shutil

from colorama import Fore, init

# Initialize colorama
init(autoreset=True, strip=False, convert=False)

def copy_model(target_directory):
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'model')
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    for item in os.listdir(model_dir):
        s = os.path.join(model_dir, item)
        d = os.path.join(target_directory, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

@click.command()
@click.argument('target_directory')
def init_command(target_directory):
    """Copies a set of template files to a target directory."""
    copy_model(target_directory)
    click.echo(f'{Fore.GREEN} Dockyman template files copied to {target_directory}')
