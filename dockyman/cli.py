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

import click
import os
import subprocess
import sys
import venv

from colorama import Fore
from dockyman.commands import (
    status, init, setup, build, clean, push, pull, run, stop
)
from dockyman.utils import get_system_version, get_local_version
from dockyman.config import DEFAULT_CONFIG_FILE, DEFAULT_CONFIG_FILE_NAME

DEFAULT_VENV_NAME = ".venv"
DISPATCHER_BYPASS_ENV = "DOCKYMAN_DISPATCHER_BYPASS"

def check_and_delegate_version(config_file, command_name):
    # Skip version check for init
    if command_name == "init":
        return

    # Skip if already dispatched
    if os.environ.get(DISPATCHER_BYPASS_ENV) == "1":
        return

    system_version = get_system_version()
    try:
        local_version = get_local_version(config_file)
    except FileNotFoundError:
        click.echo(f"{Fore.RED}[x] Config file not found: {config_file}")
        sys.exit(1)

    project_dir = os.path.dirname(os.path.abspath(config_file))
    venv_dir = os.path.join(project_dir, DEFAULT_VENV_NAME)
    dockyman_bin = os.path.join(venv_dir, "bin", "dockyman")
    
    print("COMPARE: ", system_version, local_version)

    if system_version != local_version:
        if os.path.exists(dockyman_bin):
            # Transparent delegation
            new_env = os.environ.copy()
            new_env[DISPATCHER_BYPASS_ENV] = "1"
            subprocess.run([dockyman_bin] + sys.argv[1:], env=new_env)
            sys.exit(0)
        else:
            click.echo(f"{Fore.YELLOW}[!] Version mismatch: Config requires v{local_version}, but system has v{system_version}.")
            if click.confirm(f"Do you want to install dockyman=={local_version} locally in {venv_dir}?"):
                create_venv_and_install(venv_dir, local_version)
                new_env = os.environ.copy()
                new_env[DISPATCHER_BYPASS_ENV] = "1"
                subprocess.run([dockyman_bin] + sys.argv[1:], env=new_env)
                sys.exit(0)
            else:
                click.echo(f"{Fore.RED}[x] Aborting due to version mismatch.")
                sys.exit(1)

def create_venv_and_install(venv_dir, version):
    click.echo(f"{Fore.LIGHTBLACK_EX}Creating virtual environment in {venv_dir}...")
    venv.create(venv_dir, with_pip=True)

    pip_exe = os.path.join(venv_dir, "bin", "pip")
    subprocess.check_call([pip_exe, "install", "--upgrade", "pip"])
    subprocess.check_call([pip_exe, "install", f"dockyman=={version}"])
    click.echo(f"{Fore.GREEN}[✓] dockyman=={version} installed in {venv_dir}")

@click.group()
@click.option('--config', '-c', default=DEFAULT_CONFIG_FILE, help=f'Path to {DEFAULT_CONFIG_FILE_NAME} config file')
@click.pass_context
def cli(ctx, config):
    ctx.obj = {'config': config}

    command_name = next((arg for arg in sys.argv[1:] if not arg.startswith("-")), None)
    if command_name:
        check_and_delegate_version(config, command_name)

    system_version = get_system_version()
    click.echo(f"\n{Fore.YELLOW}Dockyman CLI - Docker Management Tool (Version: {system_version})\n")

# Register commands
cli.add_command(init.init_command, 'init')
cli.add_command(setup.setup_command, 'setup')
cli.add_command(status.status_command, 'status')
cli.add_command(build.build_command, 'build')
cli.add_command(clean.clean_command, 'clean')
cli.add_command(push.push_command, 'push')
cli.add_command(pull.pull_command, 'pull')
cli.add_command(run.run_command, 'run')
cli.add_command(stop.stop_command, 'stop')

def main():
    cli()

if __name__ == '__main__':
    main()
