# MIT License
#
# Copyright (c) 2025 Istituto Italiano di Tecnologia (IIT)
#                    Author: Davide De Tommaso (davide.detommaso@iit.it)
#                    Project: Dockyman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


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
