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
import paramiko
import yaml
import re
from urllib.parse import urlparse
from dockyman._version import __version__

from colorama import Fore

def resolve_nodes_value(value):
    match = re.match(r'\$\{([^}]+)\}', str(value))
    return os.getenv(match.group(1), value) if match else value

class Node:
    def __init__(self, id, host, user, docker_daemon_address, ssh_port):
        self.id = id
        self.host = host
        self.user = user
        self.docker_daemon_address = docker_daemon_address
        self.ssh_port = ssh_port
        self.ssh_address = f"{self.user}@{self.host}:{self.ssh_port}"

    def __repr__(self):
        return f"<Node(id={self.id}, host={self.host}, user={self.user}, ssh_port={self.ssh_port})>"

class Manager(Node):
    pass

class Worker(Node):
    pass

class SwarmConfig:
    def __init__(self, manager, workers):
        self.manager = manager
        self.workers = workers

    @classmethod
    def from_dict(cls, data):
        manager = None
        workers = []
        swarm = data.get("swarm", {})

        if "manager" in swarm:
            m = swarm["manager"]
            manager = Manager(
                id=str(resolve_nodes_value(m["id"])),
                host=str(resolve_nodes_value(m["host"])),
                user=str(resolve_nodes_value(m["user"])),
                docker_daemon_address=str(resolve_nodes_value(m["docker_daemon_address"])),
                ssh_port=int(resolve_nodes_value(m["ssh_port"]))
            )
        for w in swarm.get("workers", []):
            workers.append(Worker(
                id=str(resolve_nodes_value(w["id"])),
                host=str(resolve_nodes_value(w["host"])),
                user=str(resolve_nodes_value(w["user"])),
                docker_daemon_address=str(resolve_nodes_value(w["docker_daemon_address"])),
                ssh_port=int(resolve_nodes_value(w["ssh_port"]))
            ))

        return cls(manager=manager, workers=workers)

    def get_node_from_id(self, node_id):
        if self.manager and self.manager.id == node_id:
            return self.manager
        return next((w for w in self.workers if w.id == node_id), None)

def load_yaml(config_file):
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    with open(config_file, "r") as f:
        return yaml.safe_load(f)

def get_swarm(config_file):
    config = load_yaml(config_file)
    return SwarmConfig.from_dict(config)

def get_system_version():
    return float(__version__)

def get_local_version(config_file):
    """Get the Dockyman version from the provided configuration file."""
    config = load_yaml(config_file)
    return float(config.get("project", {}).get("dockyman_version", "Unknown"))

def get_compose_paths(config_file, target="base"):
    config = load_yaml(config_file)
    project = config.get("project", {})
    context_dir = project.get("context", os.path.dirname(config_file))

    target_config = project["build"][target]
    base_path = os.path.dirname(config_file)

    compose_file = os.path.normpath(os.path.join(base_path, context_dir, target_config["compose_file"]))
    env_file = target_config.get("env_file")
    env_file = os.path.normpath(os.path.join(base_path, context_dir, env_file)) if env_file else None

    return compose_file, env_file

def get_dockyman_base_config(config_file):
    return get_compose_paths(config_file, target="base")

def get_dockyman_local_config(config_file):
    compose, _ = get_compose_paths(config_file, target="local")
    return compose

def get_dockyman_runtime_config(config_file):
    return get_compose_paths(config_file, target="runtime")

def run_ssh_command(ssh_address, command):
    try:
        url = urlparse(f"ssh://{ssh_address}")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=url.hostname, username=url.username, port=url.port or 22, allow_agent=False)

        click.echo(f"\t{Fore.LIGHTBLACK_EX}[.] Executing command: {command}")
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode().strip()
        exit_status = stdout.channel.recv_exit_status()
        ssh.close()

        if exit_status != 0:
            error = stderr.read().decode().strip()
            click.echo(f"\t{Fore.YELLOW}[!] Command failed: {error}")
            return False
        return result
    except Exception as e:
        click.echo(f"\t{Fore.RED}[x] SSH error: {e}")
        return False

def load_env_variables(env_file):
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    return env_vars

def generate_env_file(file_path, env_vars):
    with open(file_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

def load_compose_file(compose_file):
    return load_yaml(compose_file)

def services_for_nodes(compose_file, swarm, env_file=None):
    services = {}
    for name, data in load_compose_file(compose_file).get('services', {}).items():
        target_node = swarm.manager
        node_label = data.get("labels", {}).get("dockyman.node")
        profiles = data.get("profiles", [])
        if node_label:
            node = swarm.get_node_from_id(node_label)
            if node:
                target_node = node

        active_profiles = get_docker_profiles(env_file) if env_file else []
        if not profiles or any(p in active_profiles for p in profiles):
            services.setdefault(target_node, []).append(name)
    return services

def services_in_profiles(compose_file, active_profiles):
    return [
        name for name, data in load_compose_file(compose_file).get("services", {}).items()
        if not data.get("profiles") or any(p in active_profiles for p in data.get("profiles"))
    ]

def get_docker_profiles(env_file):
    return load_env_variables(env_file).get("COMPOSE_PROFILES", "").split(',')

def load_extra_env_vars_from_dockyman(config_file):
    config = load_yaml(config_file)
    extra = {}
    for item in config.get("environments_extra", []):
        if "=" in item:
            key, value = item.split("=", 1)
            extra[key.strip()] = value.strip()
    return extra
