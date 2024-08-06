import yaml
import shutil
import os
import paramiko
from urllib.parse import urlparse

def load_hosts_config(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

def copy_model(target_directory):
    model_dir = os.path.join(os.path.dirname(__file__), 'model')
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    for item in os.listdir(model_dir):
        s = os.path.join(model_dir, item)
        d = os.path.join(target_directory, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

def run_ssh_command(host, command):
    url = urlparse(host)
    hostname = url.hostname
    username = url.username
    port = url.port if url.port else 22  # Default to port 22 if not specified

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, username=username, port=port)

    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        raise Exception(f"Command failed on {host}: {stderr.read().decode()}")

    result = stdout.read().decode()
    ssh.close()
    return result

def install_docker(host):
    commands = [
        "curl -fsSL https://get.docker.com -o get-docker.sh",
        "sh get-docker.sh",
        "sudo usermod -aG docker $USER"
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
