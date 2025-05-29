import os
import subprocess
import tempfile
import shutil
import yaml
import pytest

@pytest.fixture
def temp_project_dir():
    project_dir = tempfile.mkdtemp()
    yaml_data = {
        "project": {
            "dockyman_version": "3.0",
            "context": "./.dockyman",  # Added context for your updated logic
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

def test_dispatcher_integration(temp_project_dir):
    project_dir = temp_project_dir
    config_file = os.path.join(project_dir, "dockyman.yaml")

    # Run the dispatcher CLI, simulating user input "y"
    result = subprocess.run(
        [os.path.abspath(".venv/bin/dockyman"), "--config", config_file, "status"],
        input="y\n",  # Auto-accept version install prompt
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60
    )

    print("\n--- STDOUT ---")
    print(result.stdout)
    print("\n--- STDERR ---")
    print(result.stderr)

    assert result.returncode == 0
    assert "Docker Management Tool" in result.stdout
