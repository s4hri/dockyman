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
from colorama import Fore
from dockyman.config import DEFAULT_TARGET_DIR

@click.command(help="Copy Dockyman template files to a target directory.")
@click.argument('target_path', required=True, default=DEFAULT_TARGET_DIR)
def init_command(target_path):
    """Copies the Dockyman template files to the specified target directory."""

    source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'model'))

    click.echo(f"{Fore.LIGHTBLACK_EX} -> Copying template files from {source_path} to {target_path}...")

    try:
        # Ensure target directory exists
        os.makedirs(target_path, exist_ok=True)

        # Copy files (overwrite if exists)
        for item in os.listdir(source_path):
            src_item = os.path.join(source_path, item)
            dest_item = os.path.join(target_path, item)
            if os.path.isdir(src_item):
                shutil.copytree(src_item, dest_item, dirs_exist_ok=True)
            else:
                shutil.copy2(src_item, dest_item)

        click.echo(f"{Fore.GREEN} [✓] Template files copied successfully to {target_path}")

    except Exception as e:
        click.echo(f"{Fore.RED} [x] Error copying template files: {e}")
        raise click.Abort()


if __name__ == "__main__":
    init_command()
