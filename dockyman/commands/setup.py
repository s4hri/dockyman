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
from colorama import Fore
from dockyman.utils import get_swarm, run_ssh_command
from dockyman.config import DEFAULT_CONFIG_FILE
from dockyman.commands.status import check_ssh_connection


@click.command(
    help="Install, uninstall, or check Docker, Docker Compose, and NVIDIA Docker on target machine(s)."
)
@click.argument('action', type=click.Choice(['install', 'uninstall', 'check']), required=True)
@click.argument('config_file', required=False, default='dockyman.yaml')
@click.option('--ssh_address', help='Target SSH address (optional)')
@click.pass_context
def setup_command(ctx, action, config_file, ssh_address):
    """Main entry point for setup command."""
    if ssh_address:
        handle_node(action, ssh_address)
    else:
        config_file = ctx.obj.get('config', DEFAULT_CONFIG_FILE)
        try:
            swarm = get_swarm(config_file)
            process_node(action, swarm.manager, "Manager")
            for worker in swarm.workers:
                process_node(action, worker, "Worker")
        except Exception as e:
            click.echo(f"{Fore.RED}[x] Error loading config: {e}")


def process_node(action, node, label="Node"):
    click.echo(f"\n{Fore.CYAN}*** {label}: {node.id} ***")
    if check_ssh_connection(node.ssh_address):
        perform_action(action, node.ssh_address)


def handle_node(action, ssh_address):
    if check_ssh_connection(ssh_address):
        perform_action(action, ssh_address)


def perform_action(action, ssh_address):
    actions = {
        'install': install_stack,
        'uninstall': uninstall_stack,
        'check': check_stack
    }
    actions[action](ssh_address)


# ------------------------------
# Stack Management
# ------------------------------

def install_stack(ssh):
    click.echo(f"\n{Fore.CYAN}*** Installing Components ***")
    install_or_skip("Docker", check_docker_installed, install_docker, ssh)
    install_or_skip("Docker Compose", check_docker_compose_installed, install_docker_compose, ssh)
    if check_nvidia_hardware(ssh):
        install_or_skip("NVIDIA Docker", check_nvidia_docker_installed, install_nvidia_docker, ssh)
    click.echo(f"\n{Fore.GREEN}✓ Installation completed on {ssh}")


def uninstall_stack(ssh):
    click.echo(f"\n{Fore.CYAN}*** Uninstalling Components ***")
    uninstall_if_present("Docker", check_docker_installed, uninstall_docker, ssh)
    uninstall_if_present("Docker Compose", check_docker_compose_installed, uninstall_docker_compose, ssh)
    if check_nvidia_hardware(ssh):
        uninstall_if_present("NVIDIA Docker", check_nvidia_docker_installed, uninstall_nvidia_docker, ssh)
    click.echo(f"\n{Fore.GREEN}✓ Uninstallation completed on {ssh}")


def check_stack(ssh):
    click.echo(f"\n{Fore.CYAN}*** Checking Stack ***")
    check_docker_installed(ssh)
    check_docker_compose_installed(ssh)
    if check_nvidia_hardware(ssh):
        check_nvidia_docker_installed(ssh)


# ------------------------------
# Helpers
# ------------------------------

def install_or_skip(name, checker, installer, ssh):
    if not checker(ssh):
        if click.confirm(f"{Fore.WHITE}Install {name} on {ssh}?"):
            installer(ssh)


def uninstall_if_present(name, checker, uninstaller, ssh):
    if checker(ssh):
        if click.confirm(f"{Fore.WHITE}Uninstall {name} from {ssh}?"):
            uninstaller(ssh)


def check_docker_installed(ssh): return _check_tool(ssh, 'docker --version', "Docker")
def check_docker_compose_installed(ssh): return _check_tool(ssh, 'docker-compose --version', "Docker Compose")
def check_nvidia_docker_installed(ssh): return _check_tool(ssh, 'nvidia-ctk --version', "NVIDIA Docker")


def check_nvidia_hardware(ssh):
    click.echo(f"{Fore.CYAN}*** Checking NVIDIA Hardware ***")
    result = run_ssh_command(ssh, 'lspci | grep -i nvidia')
    click.echo(f"{Fore.GREEN if result else Fore.YELLOW} {'NVIDIA hardware detected.' if result else 'No NVIDIA hardware found.'}")
    return result


def _check_tool(ssh, command, name):
    result = run_ssh_command(ssh, command)
    if result:
        click.echo(f"\t{Fore.GREEN}[✓] {name} is installed.")
    else:
        click.echo(f"\t{Fore.YELLOW}[!] {name} is not installed.")
    return result


# ------------------------------
# Install/Uninstall Commands
# ------------------------------

def install_docker(ssh):
    commands = [
        "curl -fsSL https://get.docker.com -o get-docker.sh",
        "sh get-docker.sh",
        "sudo usermod -aG docker $USER"
    ]
    _run_commands(ssh, commands)


def uninstall_docker(ssh):
    commands = [
        "sudo apt-get remove -y docker docker-engine docker.io containerd runc",
        "sudo apt-get purge -y docker-ce docker-ce-cli containerd.io",
        "sudo rm -rf /var/lib/docker"
    ]
    _run_commands(ssh, commands)


def install_docker_compose(ssh):
    commands = [
        "sudo curl -L \"https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose",
        "sudo chmod +x /usr/local/bin/docker-compose"
    ]
    _run_commands(ssh, commands)


def uninstall_docker_compose(ssh):
    _run_commands(ssh, ["sudo rm /usr/local/bin/docker-compose"])


def install_nvidia_docker(ssh):
    _run_commands(ssh, [
        "curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor --batch --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg",
        "curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list",
        "sudo apt-get update",
        "sudo apt-get install -y nvidia-container-toolkit",
        "sudo nvidia-ctk runtime configure --runtime=docker",
        "sudo systemctl restart docker"
    ])


def uninstall_nvidia_docker(ssh):
    _run_commands(ssh, [
        "sudo apt-get -y remove --purge nvidia-docker2 nvidia-container-toolkit",
        "sudo apt-get -y autoremove",
        "sudo rm -f /etc/systemd/system/docker.service.d/10-nvidia-docker.conf",
        "sudo rm -f /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg",
        "sudo rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list",
        "sudo rm -f /usr/bin/nvidia-ctk",
        "sudo rm -f /usr/bin/nvidia-container-runtime",
        "sudo rm -f /usr/bin/nvidia-container-toolkit",
        "sudo rm -rf /var/lib/nvidia-docker",
        "sudo systemctl daemon-reload",
        "sudo systemctl restart docker || true"
    ])


def _run_commands(ssh, commands):
    for cmd in commands:
        try:
            run_ssh_command(ssh, cmd)
        except Exception as e:
            click.echo(f"{Fore.YELLOW} Warning: {e}")


if __name__ == "__main__":
    setup_command()
