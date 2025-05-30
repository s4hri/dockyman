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
from python_on_whales import DockerClient
from colorama import Fore
from dockyman.utils import get_swarm, run_ssh_command, get_local_version, Node
from dockyman.config import DEFAULT_TARGET_DIR, DEFAULT_CONFIG_FILE_NAME, DEFAULT_CONFIG_FILE

@click.command()
@click.option('--ssh_address', help='Directly test an SSH address', required=False)
@click.option('--docker_daemon_address', help='Directly test a Docker daemon address', required=False)
@click.pass_context
def status_command(ctx, ssh_address, docker_daemon_address):
    """
    Check the status of Docker Swarm nodes defined in the dockyman.yaml config,
    or test specific addresses directly using --ssh_address / --docker_daemon_address.
    """
    config_file = ctx.obj.get('config', DEFAULT_CONFIG_FILE)

    if ssh_address or docker_daemon_address:
        if ssh_address:
            check_ssh_connection(ssh_address)
        if docker_daemon_address:
            check_docker_daemon(docker_daemon_address)
    else:
        try:
            local_version = get_local_version(config_file)
            click.echo(f"{Fore.LIGHTBLACK_EX}Config file: {config_file} (Version: {local_version})\n")    

            swarm = get_swarm(config_file)
            click.echo(f"{Fore.CYAN}*** Checking Manager Node: {swarm.manager.id} ***")
            check_node(swarm.manager)

            for worker in swarm.workers:
                click.echo(f"{Fore.CYAN}*** Checking Worker Node: {worker.id} ***")
                check_node(worker)
        
        except FileNotFoundError:
            click.echo(f"{Fore.RED}[x] Error: Config file not found: {config_file}")
            click.echo(f"{Fore.RED}[x] Please ensure the file exists and is accessible.")

        except Exception as e:
            click.echo(f"{Fore.RED}[x] Error: {e}")

def check_node(node: Node):
    """Run full check (SSH + Docker) for a single node."""
    check_ssh_connection(node.ssh_address)
    check_docker_daemon(node.docker_daemon_address)

def check_ssh_connection(ssh_address):
    """Test SSH connectivity to a node."""
    click.echo(f"\n{Fore.WHITE} -> Checking SSH connection with: {ssh_address} ...")
    ssh_status = run_ssh_command(ssh_address, "echo 'SSH connection test'")

    if ssh_status:
        click.echo(f"\t{Fore.GREEN}[✓] SSH connection to {ssh_address} successful!")
        return True
    else:
        click.echo(f"\t{Fore.RED}[x] SSH connection to {ssh_address} failed.")
        return False

def check_docker_daemon(docker_daemon_address):
    """Test Docker daemon accessibility via python-on-whales."""
    click.echo(f"\n{Fore.WHITE} -> Checking Docker Daemon: {docker_daemon_address} ...")

    try:
        docker = DockerClient(host=docker_daemon_address)
        version_info = docker.version()
        click.echo(f"\t{Fore.LIGHTBLACK_EX}[.] Host Docker version: {version_info.server.version}")
        click.echo(f"\t{Fore.LIGHTBLACK_EX}[.] Client Docker version: {version_info.client.version}")
        click.echo(f"\t{Fore.GREEN}[✓] Docker daemon at {docker_daemon_address} is responding!")
        return True
    except Exception as e:
        click.echo(f"\t{Fore.RED}[x] Docker Daemon Error: {str(e)}")
        return False

if __name__ == '__main__':
    status_command()
