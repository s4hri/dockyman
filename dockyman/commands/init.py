import os
import shutil
import click
from colorama import Fore, init as colorama_init

# Initialize colorama
colorama_init(autoreset=True, strip=False, convert=False)

@click.command()
@click.argument('target_directory')
def init_command(target_directory):
    """Copies a set of template files to a target directory."""

    target_directory = os.path.join("/shared", target_directory)
    
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
    local_uid = int(os.getenv('LOCAL_UID', 1000))
    local_gid = int(os.getenv('LOCAL_GID', 1000))
    click.echo(f"{Fore.LIGHTBLACK_EX}Changing ownership to UID: {local_uid} and GID: {local_gid}")

    os.chown(target_directory, local_uid, local_gid)
    for root, dirs, files in os.walk(target_directory):
        for dir_ in dirs:
            os.chown(os.path.join(root, dir_), local_uid, local_gid)
        for file_ in files:
            os.chown(os.path.join(root, file_), local_uid, local_gid)

    click.echo(f'{Fore.GREEN}Dockyman template files copied to {target_directory} with ownership changed to UID:{local_uid} and GID:{local_gid}')

if __name__ == "__main__":
    init_command()
