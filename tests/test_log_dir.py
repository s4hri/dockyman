"""Tests for logging directory resolution in load_config."""

from __future__ import annotations

import textwrap
from pathlib import Path

from dockyman.config import load_config


def _yaml(log_config: str) -> str:
    return textwrap.dedent(f"""\
        project:
          name: test
          dockyman_repo: https://github.com/youruser/dockyman
          dockyman_ref: v4.0.0
          {log_config}
          swarm:
            - node_id: manager
              compose_files: [compose.yaml]
    """)


class TestLogDirBackwardCompatibility:
    """Test backward compatibility with old log_dir field."""
    
    def test_log_dir_sets_both_directories(self, tmp_path):
        """Old log_dir field should set both container_log_dir and config_log_dir."""
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml("log_dir: logs"))
        project = load_config(str(f))
        expected = str(tmp_path / "logs")
        assert project.container_log_dir == expected
        assert project.config_log_dir == expected

    def test_log_dir_absolute_path(self, tmp_path):
        abs_path = str(tmp_path / "custom" / "logs")
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml(f"log_dir: {abs_path}"))
        project = load_config(str(f))
        assert project.container_log_dir == abs_path
        assert project.config_log_dir == abs_path

    def test_log_dir_empty_disables_all(self, tmp_path):
        """Empty log_dir disables all logging."""
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml('log_dir: ""'))
        project = load_config(str(f))
        assert project.container_log_dir == ""
        assert project.config_log_dir == ""


class TestSeparateLogDirectories:
    """Test new separate container_log_dir and config_log_dir fields."""
    
    def test_separate_directories_resolved(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml("""container_log_dir: logs/containers
          config_log_dir: logs/config"""))
        project = load_config(str(f))
        assert project.container_log_dir == str(tmp_path / "logs" / "containers")
        assert project.config_log_dir == str(tmp_path / "logs" / "config")

    def test_only_container_log_enabled(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml("container_log_dir: logs/containers"))
        project = load_config(str(f))
        assert project.container_log_dir == str(tmp_path / "logs" / "containers")
        assert project.config_log_dir == ""

    def test_only_config_log_enabled(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml("config_log_dir: logs/config"))
        project = load_config(str(f))
        assert project.container_log_dir == ""
        assert project.config_log_dir == str(tmp_path / "logs" / "config")

    def test_omitted_defaults_to_empty(self, tmp_path):
        """No log directories specified means all logging off by default."""
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml(""))  # no log config at all
        project = load_config(str(f))
        assert project.container_log_dir == ""
        assert project.config_log_dir == ""

    def test_new_fields_override_old_log_dir(self, tmp_path):
        """New fields take precedence over old log_dir for backward compat."""
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml("""log_dir: old_logs
          container_log_dir: new_containers
          config_log_dir: new_config"""))
        project = load_config(str(f))
        assert project.container_log_dir == str(tmp_path / "new_containers")
        assert project.config_log_dir == str(tmp_path / "new_config")

    def test_nested_config_dir_resolves_correctly(self, tmp_path):
        sub = tmp_path / "project" / "config"
        sub.mkdir(parents=True)
        f = sub / "dockyman.yaml"
        f.write_text(_yaml("container_log_dir: logs"))
        project = load_config(str(f))
        assert project.container_log_dir == str(sub / "logs")
