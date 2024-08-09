import click
from dockyman.utils import run_ssh_command
from colorama import Fore, init
from dockyman.config import SSH_LOCAL_USERNAME

# Initialize colorama
init(autoreset=True, strip=False, convert=False)

@click.command(help="Installs, uninstalls, or checks Docker, Docker Compose, and NVIDIA Docker (if applicable) on the target machine(s).")
@click.argument('action', type=click.Choice(['install', 'uninstall', 'check']), required=True)
@click.argument('host', required=False, default='ssh://%s@localhost' % SSH_LOCAL_USERNAME)
def setup_command(action, host):
    """Installs, uninstalls, or checks Docker, Docker Compose, and NVIDIA Docker (if applicable) on the target machine(s)."""
    
    ssh_address = host

    if action == 'install':
        click.echo(f"\n{Fore.CYAN}*** Checking Docker on {host} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX}  Checking Docker installation...")
        if is_docker_installed(ssh_address):
            question = f'{Fore.WHITE}> Docker is installed on {host}. Do you want to uninstall it first?'
            if click.confirm(question):
                click.echo(f'{Fore.YELLOW}  Uninstalling Docker on {host}...')
                uninstall_docker(ssh_address)
                click.echo(f'{Fore.GREEN}  Installing Docker on {host}...')
                install_docker(ssh_address)
            else:
                click.echo(f'{Fore.YELLOW}  Docker will not be uninstalled from {host}.')
        else:
            question = f'{Fore.WHITE}> Docker is not installed on {host}. Do you want to install it?'
            if click.confirm(question):
                click.echo(f'{Fore.GREEN}  Installing Docker on {host}...')
                install_docker(ssh_address)

        click.echo(f"\n{Fore.CYAN}*** Checking Docker Compose on {host} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX}  Checking Docker Compose installation...")
        if is_docker_compose_installed(ssh_address):
            question = f'{Fore.WHITE}> Docker Compose is installed on {host}. Do you want to uninstall it first?'
            if click.confirm(question):
                click.echo(f'{Fore.YELLOW}  Uninstalling Docker Compose on {host}...')
                uninstall_docker_compose(ssh_address)
                click.echo(f'{Fore.GREEN}  Installing Docker Compose on {host}...')
                install_docker_compose(ssh_address)
            else:
                click.echo(f'{Fore.YELLOW}  Docker Compose will not be uninstalled from {host}.')
        else:
            question = f'{Fore.WHITE}> Docker Compose is not installed on {host}. Do you want to install it?'
            if click.confirm(question):
                click.echo(f'{Fore.GREEN}  Installing Docker Compose on {host}...')
                install_docker_compose(ssh_address)
        
        click.echo(f"\n{Fore.CYAN}*** Checking NVIDIA Docker on {host} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX}  Checking NVIDIA hardware...")
        if has_nvidia_hardware(ssh_address):
            click.echo(f"{Fore.LIGHTBLACK_EX}  Checking NVIDIA Docker installation...")
            if is_nvidia_docker_installed(ssh_address):
                question = f'{Fore.WHITE}> NVIDIA Docker is installed on {host}. Do you want to uninstall it first?'
                if click.confirm(question):
                    click.echo(f'{Fore.YELLOW}  Uninstalling NVIDIA Docker on {host}...')
                    uninstall_nvidia_docker(ssh_address)
                    click.echo(f'{Fore.GREEN}  Installing NVIDIA Docker on {host}...')
                    install_nvidia_docker(ssh_address)
                else:
                    click.echo(f'{Fore.YELLOW}  NVIDIA Docker will not be uninstalled from {host}.')
            else:
                question = f'{Fore.WHITE}> NVIDIA Docker is not installed on {host}. Do you want to install it?'
                if click.confirm(question):
                    click.echo(f'{Fore.GREEN}  Installing NVIDIA Docker on {host}...')
                    install_nvidia_docker(ssh_address)
        
        click.echo(f'\n{Fore.CYAN}*** Setup completed on {host} ***')

    elif action == 'uninstall':
        click.echo(f"\n{Fore.CYAN}*** Uninstalling Docker on {host} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX}  Checking Docker installation...")
        if is_docker_installed(ssh_address):
            question = f'{Fore.WHITE}> Docker is installed on {host}. Do you want to uninstall it?'
            if click.confirm(question):
                click.echo(f'{Fore.YELLOW}  Uninstalling Docker on {host}...')
                uninstall_docker(ssh_address)
            else:
                click.echo(f'{Fore.YELLOW}  Docker will not be uninstalled from {host}.')
        else:
            click.echo(f"{Fore.YELLOW}  Docker is not installed on {host}.")

        click.echo(f"\n{Fore.CYAN}*** Uninstalling Docker Compose on {host} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX}  Checking Docker Compose installation...")
        if is_docker_compose_installed(ssh_address):
            question = f'{Fore.WHITE}> Docker Compose is installed on {host}. Do you want to uninstall it?'
            if click.confirm(question):
                click.echo(f'{Fore.YELLOW}  Uninstalling Docker Compose on {host}...')
                uninstall_docker_compose(ssh_address)
            else:
                click.echo(f'{Fore.YELLOW}  Docker Compose will not be uninstalled from {host}.')
        else:
            click.echo(f"{Fore.YELLOW}  Docker Compose is not installed on {host}.")

        click.echo(f"\n{Fore.CYAN}*** Uninstalling NVIDIA Docker on {host} ***")
        click.echo(f"{Fore.LIGHTBLACK_EX}  Checking NVIDIA Docker installation...")
        if has_nvidia_hardware(ssh_address):
            if is_nvidia_docker_installed(ssh_address):
                question = f'{Fore.WHITE}> NVIDIA Docker is installed on {host}. Do you want to uninstall it?'
                if click.confirm(question):
                    click.echo(f'{Fore.YELLOW}  Uninstalling NVIDIA Docker on {host}...')
                    uninstall_nvidia_docker(ssh_address)
                else:
                    click.echo(f'{Fore.YELLOW}  NVIDIA Docker will not be uninstalled from {host}.')
            else:
                click.echo(f"{Fore.YELLOW}  NVIDIA Docker is not installed on {host}.")
        
        click.echo(f'\n{Fore.CYAN}*** Uninstallation completed on {host} ***')

    elif action == 'check':
        click.echo(f"\n{Fore.CYAN}*** Checking Docker on {host} ***")
        if is_docker_installed(ssh_address):
            click.echo(f"{Fore.GREEN}  Docker is installed.")
        else:
            click.echo(f"{Fore.RED}  Docker is not installed.")

        click.echo(f"\n{Fore.CYAN}*** Checking Docker Compose on {host} ***")
        if is_docker_compose_installed(ssh_address):
            click.echo(f"{Fore.GREEN}  Docker Compose is installed.")
        else:
            click.echo(f"{Fore.RED}  Docker Compose is not installed.")

        click.echo(f"\n{Fore.CYAN}*** Checking NVIDIA Docker on {host} ***")
        if has_nvidia_hardware(ssh_address):
            if is_nvidia_docker_installed(ssh_address):
                click.echo(f"{Fore.GREEN}  NVIDIA Docker is installed.")
            else:
                click.echo(f"{Fore.RED}  NVIDIA Docker is not installed.")
        else:
            click.echo(f"{Fore.RED}  NVIDIA hardware not detected.")
        
        click.echo(f'\n{Fore.CYAN}*** Check completed on {host} ***')

def is_docker_service_present(host):
    try:
        run_ssh_command(host, 'systemctl status docker.service')
        return True
    except Exception as e:
        return False
    
def is_docker_installed(host):
    return run_ssh_command(host, 'docker --version')

def is_docker_compose_installed(host):
    return run_ssh_command(host, 'docker-compose  --version')

def has_nvidia_hardware(host):
    return run_ssh_command(host, 'lspci | grep -i nvidia')

def is_nvidia_docker_installed(host):
    try:
        run_ssh_command(host, 'nvidia-ctk --version')
        return True
    except Exception as e:
        click.echo(f"{Fore.YELLOW}  NVIDIA Container Toolkit not installed.")
        return False

def install_docker(host):
    commands = [
        "curl -fsSL https://get.docker.com -o get-docker.sh",
        "sh get-docker.sh",
        "sudo usermod -aG docker $USER"
    ]
    for command in commands:
        run_ssh_command(host, command)

def uninstall_docker(host):
    commands = [
        "sudo apt-get remove -y docker docker-engine docker.io containerd runc",
        "sudo apt-get purge -y docker-ce docker-ce-cli containerd.io",
        "sudo rm -rf /var/lib/docker"
    ]
    for command in commands:
        run_ssh_command(host, command)

def install_docker_compose(host):
    commands = [
        "sudo curl -L \"https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose",
        "sudo chmod +x /usr/local/bin/docker-compose"
    ]
    for command in commands:
        run_ssh_command(host, command)

def uninstall_docker_compose(host):
    commands = [
        "sudo rm /usr/local/bin/docker-compose"
    ]
    for command in commands:
        run_ssh_command(host, command)

def install_nvidia_container_toolkit(host):
    """Install the NVIDIA Container Toolkit on the target host."""
    commands = [
        "curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor --batch --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg",
        "curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list",
        "sudo apt-get update",
        "sudo apt-get install -y nvidia-container-toolkit"
    ]
    for command in commands:
        run_ssh_command(host, command)

    # Check if nvidia-ctk is installed
    try:
        run_ssh_command(host, "which nvidia-ctk")
    except Exception as e:
        raise Exception(f"nvidia-ctk command not found on {host}: {str(e)}")

    configure_nvidia_runtime(host)

def configure_nvidia_runtime(host):
    """Configure the NVIDIA runtime for Docker on the target host."""
    commands = [
        "sudo nvidia-ctk runtime configure --runtime=docker",
        "sudo systemctl restart docker"
    ]
    for command in commands:
        run_ssh_command(host, command)

def install_nvidia_docker(host):
    """Install NVIDIA Docker including configuring the runtime and restarting Docker."""
    install_nvidia_container_toolkit(host)
    configure_nvidia_runtime(host)

def uninstall_nvidia_docker(host):
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
            run_ssh_command(host, command)
        except Exception as e:
            click.echo(f"{Fore.YELLOW}  Warning: {str(e)}")
    
    # Only restart Docker if the Docker service unit is present
    if is_docker_service_present(host):
        try:
            run_ssh_command(host, "sudo systemctl restart docker")
        except Exception as e:
            click.echo(f"{Fore.YELLOW}  Warning: Could not restart Docker service: {str(e)}")

if __name__ == "__main__":
    setup_command()
