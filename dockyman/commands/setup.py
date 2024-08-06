import click
from dockyman.utils import load_hosts_config, run_ssh_command

@click.command(help="Installs or uninstalls Docker, Docker Compose, and NVIDIA Docker (if applicable) on the target machine(s).")
@click.argument('host', required=False)
def setup_command(host):
    """Installs or uninstalls Docker, Docker Compose, and NVIDIA Docker (if applicable) on the target machine(s)."""
    hosts_config = load_hosts_config('hosts.yml')
    
    if host:
        hosts = [host]
    else:
        hosts = hosts_config['hosts'].keys()
    
    for h in hosts:
        host_config = hosts_config['hosts'][h]
        ssh_address = host_config['ssh']
        
        # Docker
        if is_docker_installed(ssh_address):
            if click.confirm(f'Docker is installed on {h}. Do you want to uninstall it?'):
                uninstall_docker(ssh_address)
            else:
                click.echo(f'Docker will not be uninstalled from {h}.')
        else:
            if click.confirm(f'Docker is not installed on {h}. Do you want to install it?'):
                install_docker(ssh_address)
        
        # Docker Compose
        if is_docker_compose_installed(ssh_address):
            if click.confirm(f'Docker Compose is installed on {h}. Do you want to uninstall it?'):
                uninstall_docker_compose(ssh_address)
            else:
                click.echo(f'Docker Compose will not be uninstalled from {h}.')
        else:
            if click.confirm(f'Docker Compose is not installed on {h}. Do you want to install it?'):
                install_docker_compose(ssh_address)
        
        # NVIDIA Docker
        if has_nvidia_hardware(ssh_address):
            if is_nvidia_docker_installed(ssh_address):
                if click.confirm(f'NVIDIA Docker is installed on {h}. Do you want to uninstall it?'):
                    uninstall_nvidia_docker(ssh_address)
                else:
                    click.echo(f'NVIDIA Docker will not be uninstalled from {h}.')
            else:
                if click.confirm(f'NVIDIA Docker is not installed on {h}. Do you want to install it?'):
                    install_nvidia_docker(ssh_address)
        
        click.echo(f'Setup completed on {h}')

def is_docker_installed(host):
    #try:
    run_ssh_command(host, 'docker --version')
    #    return True
    #except Exception:
    #    return False

def is_docker_compose_installed(host):
    try:
        run_ssh_command(host, 'docker-compose --version')
        return True
    except Exception:
        return False

def has_nvidia_hardware(host):
    try:
        run_ssh_command(host, 'lspci | grep -i nvidia')
        return True
    except Exception:
        return False

def is_nvidia_docker_installed(host):
    try:
        run_ssh_command(host, 'nvidia-container-runtime --version')
        return True
    except Exception:
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
        "sudo curl -L \"https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose",
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

def install_nvidia_docker(host):
    commands = [
        "distribution=$(. /etc/os-release;echo $ID$VERSION_ID)",
        "curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -",
        "curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list",
        "sudo apt-get update",
        "sudo apt-get install -y nvidia-container-toolkit",
        "sudo systemctl restart docker"
    ]
    for command in commands:
        run_ssh_command(host, command)

def uninstall_nvidia_docker(host):
    commands = [
        "sudo apt-get remove -y nvidia-container-toolkit",
        "sudo rm /etc/systemd/system/docker.service.d/10-nvidia-docker.conf",
        "sudo systemctl daemon-reload",
        "sudo systemctl restart docker"
    ]
    for command in commands:
        run_ssh_command(host, command)
