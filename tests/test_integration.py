import os
import subprocess
import tempfile
import shutil
import yaml
import pytest

@pytest.fixture
def temp_project_dir():
    project_dir = tempfile.mkdtemp()

    # Create context folder structure
    context_dir = os.path.join(project_dir, ".")
    os.makedirs(os.path.join(context_dir, "base"), exist_ok=True)
    os.makedirs(os.path.join(context_dir, "local"), exist_ok=True)

    # Create dummy files in context
    with open(os.path.join(context_dir, "base", "compose.yaml"), "w") as f:
        f.write("version: '3.8'\nservices:\n  dummy:\n    image: alpine")

    with open(os.path.join(context_dir, "local", "compose.yaml"), "w") as f:
        f.write("version: '3.8'\nservices:\n  dummy:\n    image: alpine")

    with open(os.path.join(context_dir, "compose.yaml"), "w") as f:
        f.write("version: '3.8'\nservices:\n  dummy:\n    image: alpine")

    with open(os.path.join(context_dir, "build.env"), "w") as f:
        f.write("DUMMY_ENV=1\n")

    # Create dockyman.yaml with context
    yaml_data = {
        "project": {
            "dockyman_version": "3.0",
            "context": "./",
            "build": {
                "base": {"compose_file": "base/compose.yaml", "env_file": "build.env"},
                "local": {"compose_file": "local/compose.yaml", "env_file": ".env"},
                "runtime": {"compose_file": "compose.yaml", "env_file": ".env", "manager_entrypoint": ".dockyman/scripts/initHost.sh"},
            }
        },
        "swarm": {
            "manager": {
                "id": "manager-node",
                "host": "127.0.0.1",
                "user": "${USER}",
                "ssh_port": 22,
                "docker_daemon_address": "unix:///var/run/docker.sock"
            },
            "workers": []
        },
        "environments_extra": ["DOCKER_LOGS=false"]
    }

    config_path = os.path.join(project_dir, "dockyman.yaml")
    with open(config_path, "w") as f:
        yaml.dump(yaml_data, f)

    yield project_dir

    shutil.rmtree(project_dir)


def test_dispatcher_integration(temp_project_dir):
    project_dir = temp_project_dir
    config_file = os.path.join(project_dir, "dockyman.yaml")

    result = subprocess.run(
        [os.path.abspath(".venv/bin/dockyman"), "--config", config_file, "status"],
        input="y\n",  # Auto-accept version install prompt
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120
    )

    print("\n--- STDOUT ---")
    print(result.stdout)
    print("\n--- STDERR ---")
    print(result.stderr)

    assert result.returncode == 0
    assert "Docker Management Tool" in result.stdout
