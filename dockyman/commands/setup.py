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
import click
from colorama import Fore
from dockyman.utils import get_swarm, run_ssh_command
from dockyman.config import PREFIX_TARGET
from dockyman.commands.status import check_ssh_connection


@click.command(
    help="Install, uninstall, or check Docker, Docker Compose, and NVIDIA Docker on target machine(s)."
)
@click.argument('action', type=click.Choice(['install', 'uninstall', 'check']), required=True)
@click.argument('config_file', required=False, default='dockyman.yaml')
@click.option('--ssh_address', help='Target SSH address (optional)')
def setup_command(action, config_file, ssh_address):
    if ssh_address:
        if check_ssh_connection(ssh_address):
            perform_action(action, ssh_address)
    else:
        try:
            config_path = os.path.join(PREFIX_TARGET, config_file)
            swarm = get_swarm(config_path)

            click.echo(f"\n{Fore.CYAN}*** Manager Node: {swarm.manager.id} ***")
            if check_ssh_connection(swarm.manager.ssh_address):
                perform_action(action, swarm.manager.ssh_address)

            for worker in swarm.workers:
                click.echo(f"\n{Fore.CYAN}*** Worker Node: {worker.id} ***")
                if check_ssh_connection(worker.ssh_address):
                    perform_action(action, worker.ssh_address)
        except Exception as e:
            click.echo(f"{Fore.RED}[x] Error loading config: {e}")


def perform_action(action, ssh_address):
    """Run the specified setup action (install, uninstall, check)."""
    if action == 'install':
        install_stack(ssh_address)
    elif action == 'uninstall':
        uninstall_stack(ssh_address)
    elif action == 'check':
        check_stack(ssh_address)


# ------------------------------
# Action Helpers
# ------------------------------

def install_stack(ssh):
    click.echo(f"\n{Fore.CYAN}*** Docker ***")
    if not check_docker_installed(ssh):
        if click.confirm(f"{Fore.WHITE}Install Docker on {ssh}?"):
            install_docker(ssh)

    click.echo(f"\n{Fore.CYAN}*** Docker Compose ***")
    if not check_docker_compose_installed(ssh):
        if click.confirm(f"{Fore.WHITE}Install Docker Compose on {ssh}?"):
            install_docker_compose(ssh)

    if check_nvidia_hardware(ssh):
        click.echo(f"\n{Fore.CYAN}*** NVIDIA Docker ***")
        if not check_nvidia_docker_installed(ssh):
            if click.confirm(f"{Fore.WHITE}Install NVIDIA Docker on {ssh}?"):
                install_nvidia_docker(ssh)

    click.echo(f"\n{Fore.GREEN}✓ Installation completed on {ssh}")


def uninstall_stack(ssh):
    click.echo(f"\n{Fore.CYAN}*** Uninstalling on {ssh} ***")

    if check_docker_installed(ssh) and click.confirm(f"{Fore.WHITE}Uninstall Docker?"):
        uninstall_docker(ssh)

    if check_docker_compose_installed(ssh) and click.confirm(f"{Fore.WHITE}Uninstall Docker Compose?"):
        uninstall_docker_compose(ssh)

    if check_nvidia_hardware(ssh) and check_nvidia_docker_installed(ssh):
        if click.confirm(f"{Fore.WHITE}Uninstall NVIDIA Docker?"):
            uninstall_nvidia_docker(ssh)

    click.echo(f"\n{Fore.GREEN}✓ Uninstallation completed on {ssh}")


def check_stack(ssh):
    click.echo(f"\n{Fore.CYAN}*** Checking Docker ***")
    check_docker_installed(ssh)

    click.echo(f"\n{Fore.CYAN}*** Checking Docker Compose ***")
    check_docker_compose_installed(ssh)

    if check_nvidia_hardware(ssh):
        click.echo(f"\n{Fore.CYAN}*** Checking NVIDIA Docker ***")
        check_nvidia_docker_installed(ssh)


# ------------------------------
# Check Utilities
# ------------------------------

def check_docker_installed(ssh): return _check_tool(ssh, 'docker --version', "Docker")
def check_docker_compose_installed(ssh): return _check_tool(ssh, 'docker-compose --version', "Docker Compose")
def check_nvidia_docker_installed(ssh): return _check_tool(ssh, 'nvidia-ctk --version', "NVIDIA Docker")


def check_nvidia_hardware(ssh):
    click.echo(f"\n{Fore.CYAN}*** Checking NVIDIA Hardware ***")
    result = run_ssh_command(ssh, 'lspci | grep -i nvidia')
    msg = "NVIDIA hardware detected." if result else "No NVIDIA hardware detected."
    color = Fore.GREEN if result else Fore.YELLOW
    click.echo(f"{color} {msg}")
    return result

def has_nvidia_hardware(ssh_address):
    """Alias for check_nvidia_hardware() for semantic clarity."""
    return check_nvidia_hardware(ssh_address)

def _check_tool(ssh, command, name):
    result = run_ssh_command(ssh, command)
    if result:
        click.echo(f"\t{Fore.GREEN}[✓] {name} is installed.")
    else:
        click.echo(f"\t{Fore.YELLOW}[!] {name} is not installed.")
    return result


# ------------------------------
# Install / Uninstall Commands
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
    install_nvidia_container_toolkit(ssh)
    configure_nvidia_runtime(ssh)


def uninstall_nvidia_docker(ssh):
    commands = [
        "sudo apt-get -y remove --purge nvidia-docker2 nvidia-container-toolkit",
        "sudo apt-get -y autoremove",
        "sudo rm -f /etc/systemd/system/docker.service.d/10-nvidia-docker.conf",
        "sudo rm -f /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg",
        "sudo rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list",
        "sudo systemctl daemon-reload",
        "sudo rm -f /usr/bin/nvidia-ctk",
        "sudo rm -f /usr/bin/nvidia-container-runtime",
        "sudo rm -f /usr/bin/nvidia-container-toolkit",
        "sudo rm -rf /var/lib/nvidia-docker"
    ]
    _run_commands(ssh, commands)
    if is_docker_service_present(ssh):
        try:
            run_ssh_command(ssh, "sudo systemctl restart docker")
        except Exception as e:
            click.echo(f"{Fore.YELLOW} Warning: Could not restart Docker service: {e}")


def install_nvidia_container_toolkit(ssh):
    commands = [
        "curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor --batch --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg",
        "curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list",
        "sudo apt-get update",
        "sudo apt-get install -y nvidia-container-toolkit"
    ]
    _run_commands(ssh, commands)


def configure_nvidia_runtime(ssh):
    commands = [
        "sudo nvidia-ctk runtime configure --runtime=docker",
        "sudo systemctl restart docker"
    ]
    _run_commands(ssh, commands)


def is_docker_service_present(ssh):
    return run_ssh_command(ssh, 'systemctl status docker.service')


def _run_commands(ssh, commands):
    for cmd in commands:
        try:
            run_ssh_command(ssh, cmd)
        except Exception as e:
            click.echo(f"{Fore.YELLOW} Warning: {e}")


if __name__ == "__main__":
    setup_command()
