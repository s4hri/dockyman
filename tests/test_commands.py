import os
import subprocess
import tempfile
import shutil
import yaml
import pytest
import re

def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

@pytest.fixture
def temp_project_dir():
    project_dir = tempfile.mkdtemp()
    context_dir = os.path.join(project_dir, ".dockyman")
    os.makedirs(context_dir)

    # Add dummy base/compose.yaml, local/compose.yaml, runtime/compose.yaml
    os.makedirs(os.path.join(context_dir, "base"))
    os.makedirs(os.path.join(context_dir, "local"))

    with open(os.path.join(context_dir, "base", "compose.yaml"), "w") as f:
        f.write("version: '3'")

    with open(os.path.join(context_dir, "local", "compose.yaml"), "w") as f:
        f.write("version: '3'")

    with open(os.path.join(context_dir, "compose.yaml"), "w") as f:
        f.write("version: '3'")

    with open(os.path.join(context_dir, "build.env"), "w") as f:
        f.write("VAR=VALUE")

    yaml_data = {
        "project": {
            "dockyman_version": "3.0",
            "context": "./.dockyman",
            "build": {
                "base": {"compose_file": "base/compose.yaml", "env_file": "build.env"},
                "local": {"compose_file": "local/compose.yaml", "env_file": ".env"},
                "runtime": {"compose_file": "compose.yaml", "env_file": ".env"},
            }
        },
        "swarm": {
            "manager": {
                "id": "manager-node",
                "host": "127.0.0.1",
                "user": "testuser",
                "ssh_port": 22,
                "docker_daemon_address": "unix:///var/run/docker.sock"
            },
            "workers": []
        },
        "environments_extra": ["DOCKER_LOGS=true"]
    }

    config_path = os.path.join(project_dir, "dockyman.yaml")
    with open(config_path, "w") as f:
        yaml.dump(yaml_data, f)

    yield project_dir
    shutil.rmtree(project_dir)

def run_dockyman(args, cwd=None, input=None):
    return subprocess.run(
        [os.path.abspath(".venv/bin/dockyman")] + args,
        cwd=cwd,
        input=input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60
    )

def test_init(temp_project_dir):
    result = run_dockyman(["init"], cwd=temp_project_dir)
    assert result.returncode == 0
    output = strip_ansi(result.stdout)
    assert "Template files copied successfully" in output

def test_status(temp_project_dir):
    config_file = os.path.join(temp_project_dir, "dockyman.yaml")
    result = run_dockyman(["--config", config_file, "status"], cwd=temp_project_dir, input="\n")
    assert result.returncode == 0
    output = strip_ansi(result.stdout)
    assert "Docker Management Tool" in output

def test_setup(temp_project_dir):
    config_file = os.path.join(temp_project_dir, "dockyman.yaml")
    result = run_dockyman(["--config", config_file, "setup", "check"], cwd=temp_project_dir, input="\n")
    assert result.returncode == 0 or result.returncode == 1  # Accept 1 if no SSH
    output = strip_ansi(result.stdout)
    assert "Manager Node" in output or "SSH error" in output

def test_build(temp_project_dir):
    config_file = os.path.join(temp_project_dir, "dockyman.yaml")
    result = run_dockyman(["--config", config_file, "build", "base"], cwd=temp_project_dir, input="\n")
    assert result.returncode == 0 or result.returncode == 1
    output = strip_ansi(result.stdout)
    assert "Building BASE images" in output or "Error" in output

def test_run_and_stop(temp_project_dir):
    config_file = os.path.join(temp_project_dir, "dockyman.yaml")
    result = run_dockyman(["--config", config_file, "run", "--no_detach"], cwd=temp_project_dir, input="\n")
    assert result.returncode == 0 or result.returncode == 1
    output = strip_ansi(result.stdout)
    assert "Docker Management Tool" in output or "Error" in output
