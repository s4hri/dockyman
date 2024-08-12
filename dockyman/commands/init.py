import os
import shutil
import click
from dockyman.config import PREFIX_TARGET, LOCAL_GID, LOCAL_UID
from colorama import Fore

@click.command()
@click.argument('target_directory')
def init_command(target_directory):
    """Copies a set of template files to a target directory."""

    click.echo(f"{Fore.LIGHTBLACK_EX} Coping template files to {target_directory} ...")
    target_directory = os.path.join(PREFIX_TARGET, target_directory)
    
    # Define the source directory inside the Docker container
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'model')
    
    # Ensure the target directory exists
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    
    # Copy the model directory to the target location
    for item in os.listdir(model_dir):
        s = os.path.join(model_dir, item)
        d = os.path.join(target_directory, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
    
    # Change ownership to the local user
    click.echo(f"{Fore.LIGHTBLACK_EX} Changing ownership to UID: {LOCAL_UID} and GID: {LOCAL_GID}")

    os.chown(target_directory, LOCAL_UID, LOCAL_GID)
    for root, dirs, files in os.walk(target_directory):
        for dir_ in dirs:
            os.chown(os.path.join(root, dir_), LOCAL_UID, LOCAL_GID)
        for file_ in files:
            os.chown(os.path.join(root, file_), LOCAL_UID, LOCAL_GID)

    click.echo(f'{Fore.GREEN} Dockyman template files copied with ownership changed to UID:{LOCAL_UID} and GID:{LOCAL_GID}')

if __name__ == "__main__":
    init_command()
