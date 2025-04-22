import click
import yaml
import os
from dockyman.utils import run_ssh_command
from colorama import Fore
from dockyman.utils import get_swarm, run_ssh_command, Node
from dockyman.config import PREFIX_TARGET
from dockyman.commands.status import check_ssh_connection

@click.command(help="Installs, uninstalls, or checks Docker, Docker Compose, and NVIDIA Docker (if applicable) on the target machine(s).")
@click.argument('action', type=click.Choice(['install', 'uninstall', 'check']), required=True)
@click.argument('nodes_file', required=False, default='nodes.yaml')
@click.option('--ssh_address', required=False)
def setup_command(action, nodes_file, ssh_address):
    """Installs, uninstalls, or checks Docker, Docker Compose, and NVIDIA Docker (if applicable) on the target machine(s)."""

    if ssh_address:
        if check_ssh_connection(ssh_address):
            perform_action(action, ssh_address)
    else:
        try:
            nodes_file_path = os.path.join(PREFIX_TARGET, nodes_file)
            swarm = get_swarm(nodes_file_path)

            # Check the manager node
            click.echo(f"\n{Fore.CYAN}*** Checking Manager Node: {swarm.manager.id} ***")
            if check_ssh_connection(swarm.manager.ssh_address):
                perform_action(action, swarm.manager.ssh_address)

            # Check the worker nodes
            for worker in swarm.workers:
                click.echo(f"\n{Fore.CYAN}*** Checking Worker Node: {worker.id} ***")
                if check_ssh_connection(worker.ssh_address):
                    perform_action(action, worker.ssh_address)
        except Exception as e:
            click.echo(f"{Fore.RED} Please provide a valid nodes file path or options.")


def perform_action(action, ssh_address):
    """Perform the specified action on the given SSH address."""

    if action == 'install':
        click.echo(f"\n{Fore.CYAN}*** Checking Docker on {ssh_address} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX} Checking Docker installation...")
        if check_docker_installed(ssh_address):
            click.echo(f'{Fore.WHITE} Docker is already installed on {ssh_address}')
        else:
            question = f'{Fore.WHITE} Docker is not installed on {ssh_address}. Do you want to install it?'
            if click.confirm(question):
                click.echo(f'{Fore.GREEN} Installing Docker on {ssh_address}...')
                install_docker(ssh_address)

        click.echo(f"\n{Fore.CYAN}*** Checking Docker Compose on {ssh_address} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX} Checking Docker Compose installation...")

        if check_docker_compose_installed(ssh_address):
            click.echo(f'{Fore.WHITE} Docker Compose is already installed on {ssh_address}')
        else:
            question = f'{Fore.WHITE} Docker Compose is not installed on {ssh_address}. Do you want to install it?'
            if click.confirm(question):
                click.echo(f'{Fore.GREEN} Installing Docker Compose on {ssh_address}...')
                install_docker_compose(ssh_address)

        click.echo(f"\n{Fore.CYAN}*** Checking NVIDIA Docker on {ssh_address} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX} Checking NVIDIA hardware...")

        if check_nvidia_hardware(ssh_address):
            click.echo(f'{Fore.GREEN} NVIDIA hardware detected.')
            if check_nvidia_docker_installed(ssh_address):
                click.echo(f'{Fore.WHITE} NVIDIA Docker is already installed on {ssh_address}')
            else:
                question = f'{Fore.WHITE} NVIDIA Docker is not installed on {ssh_address}. Do you want to install it?'
                if click.confirm(question):
                    click.echo(f'{Fore.GREEN} Installing NVIDIA Docker on {ssh_address}...')
                    install_nvidia_docker(ssh_address)

        click.echo(f'\n{Fore.CYAN}*** Setup completed on {ssh_address} ***')

    elif action == 'uninstall':
        click.echo(f"\n{Fore.CYAN}*** Uninstalling Docker on {ssh_address} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX} Checking Docker installation...")

        if check_docker_installed(ssh_address):
            question = f'{Fore.WHITE} Docker is installed on {ssh_address}. Do you want to uninstall it?'
            if click.confirm(question):
                click.echo(f'{Fore.YELLOW} Uninstalling Docker on {ssh_address}...')
                uninstall_docker(ssh_address)
            else:
                click.echo(f'{Fore.YELLOW} Docker will not be uninstalled from {ssh_address}.')

        if check_docker_compose_installed(ssh_address):
            question = f'{Fore.WHITE} Docker Compose is installed on {ssh_address}. Do you want to uninstall it?'
            if click.confirm(question):
                click.echo(f'{Fore.YELLOW} Uninstalling Docker Compose on {ssh_address}...')
                uninstall_docker_compose(ssh_address)
            else:
                click.echo(f'{Fore.YELLOW} Docker Compose will not be uninstalled from {ssh_address}.')

        if check_nvidia_hardware(ssh_address):
            if check_nvidia_docker_installed(ssh_address):
                question = f'{Fore.WHITE} NVIDIA Docker is installed on {ssh_address}. Do you want to uninstall it?'
                if click.confirm(question):
                    click.echo(f'{Fore.YELLOW} Uninstalling NVIDIA Docker on {ssh_address}...')
                    uninstall_nvidia_docker(ssh_address)
                else:
                    click.echo(f'{Fore.YELLOW} NVIDIA Docker will not be uninstalled from {ssh_address}.')

        click.echo(f'\n{Fore.CYAN}*** Uninstall completed on {ssh_address} ***')

    elif action == 'check':
        click.echo(f"\n{Fore.CYAN}*** Checking Docker on {ssh_address} ***")
        check_docker_installed(ssh_address)

        click.echo(f"\n{Fore.CYAN}*** Checking Docker Compose on {ssh_address} ***")
        check_docker_compose_installed(ssh_address)

        click.echo(f"\n{Fore.CYAN}*** Checking NVIDIA Docker on {ssh_address} ***")
        if check_nvidia_hardware(ssh_address):
            check_nvidia_docker_installed(ssh_address)

def is_docker_service_present(host):
    return run_ssh_command(host, 'systemctl status docker.service')

def check_nvidia_hardware(ssh_address):
    res = run_ssh_command(ssh_address, 'lspci | grep -i nvidia')
    if res:
        click.echo(f"{Fore.GREEN} NVIDIA hardware detected.")
    else:
        click.echo(f"{Fore.YELLOW} NVIDIA hardware not detected.")
    return res

def has_nvidia_hardware(ssh_address):
    return check_nvidia_hardware(ssh_address)

def check_nvidia_docker_installed(ssh_address):
    res = run_ssh_command(ssh_address, 'nvidia-ctk --version')
    if res:
        click.echo(f"{Fore.GREEN} NVIDIA Container Toolkit is installed.")
    else:
        click.echo(f"{Fore.YELLOW} NVIDIA Container Toolkit not installed.")
    return res

def check_docker_installed(ssh_address):
    res = run_ssh_command(ssh_address, 'docker --version')
    if res:
        click.echo(f"{Fore.GREEN} Docker is installed.")
    else:
        click.echo(f"{Fore.YELLOW} Docker is not installed.")
    return res

def check_docker_compose_installed(ssh_address):
    res = run_ssh_command(ssh_address, 'docker-compose --version')
    if res:
        click.echo(f"{Fore.GREEN} Docker Compose is installed.")
    else:
        click.echo(f"{Fore.YELLOW} Docker Compose is not installed.")
    return res

def install_docker(ssh_address):
    commands = [
        "curl -fsSL https://get.docker.com -o get-docker.sh",
        "sh get-docker.sh",
        "sudo usermod -aG docker $USER"
    ]
    for command in commands:
        run_ssh_command(ssh_address, command)

def uninstall_docker(ssh_address):
    commands = [
        "sudo apt-get remove -y docker docker-engine docker.io containerd runc",
        "sudo apt-get purge -y docker-ce docker-ce-cli containerd.io",
        "sudo rm -rf /var/lib/docker"
    ]
    for command in commands:
        run_ssh_command(ssh_address, command)

def install_docker_compose(ssh_address):
    commands = [
        "sudo curl -L \"https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose",
        "sudo chmod +x /usr/local/bin/docker-compose"
    ]
    for command in commands:
        run_ssh_command(ssh_address, command)

def uninstall_docker_compose(ssh_address):
    commands = [
        "sudo rm /usr/local/bin/docker-compose"
    ]
    for command in commands:
        run_ssh_command(ssh_address, command)

def install_nvidia_container_toolkit(ssh_address):
    """Install the NVIDIA Container Toolkit on the target host."""
    commands = [
        "curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor --batch --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg",
        "curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list",
        "sudo apt-get update",
        "sudo apt-get install -y nvidia-container-toolkit"
    ]
    for command in commands:
        run_ssh_command(ssh_address, command)

    if check_nvidia_docker_installed(ssh_address):
        configure_nvidia_runtime(ssh_address)

def configure_nvidia_runtime(ssh_address):
    """Configure the NVIDIA runtime for Docker on the target host."""
    commands = [
        "sudo nvidia-ctk runtime configure --runtime=docker",
        "sudo systemctl restart docker"
    ]
    for command in commands:
        run_ssh_command(ssh_address, command)

def install_nvidia_docker(ssh_address):
    """Install NVIDIA Docker including configuring the runtime and restarting Docker."""
    install_nvidia_container_toolkit(ssh_address)
    configure_nvidia_runtime(ssh_address)

def uninstall_nvidia_docker(ssh_address):
    """Uninstall NVIDIA Docker and related components on the target host."""
    commands = [
        "sudo apt-get -y remove --purge nvidia-docker2 nvidia-container-toolkit",
        "sudo apt-get -y autoremove",
        "sudo rm -f /etc/systemd/system/docker.service.d/10-nvidia-docker.conf",
        "sudo rm -f /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg",
        "sudo rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list",
        "sudo systemctl daemon-reload",
        "sudo rm -f /usr/bin/nvidia-ctk",  # Attempt to remove any remaining binaries
        "sudo rm -f /usr/bin/nvidia-container-runtime",  # Remove additional binaries if they exist
        "sudo rm -f /usr/bin/nvidia-container-toolkit",  # Remove additional binaries if they exist
        "sudo rm -rf /var/lib/nvidia-docker"
    ]

    for command in commands:
        try:
            run_ssh_command(ssh_address, command)
        except Exception as e:
            click.echo(f"{Fore.YELLOW}  Warning: {str(e)}")

    # Only restart Docker if the Docker service unit is present
    if is_docker_service_present(ssh_address):
        try:
            run_ssh_command(ssh_address, "sudo systemctl restart docker")
        except Exception as e:
            click.echo(f"{Fore.YELLOW}  Warning: Could not restart Docker service: {str(e)}")

if __name__ == "__main__":
    setup_command()
