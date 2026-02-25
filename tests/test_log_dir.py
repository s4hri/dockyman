"""Tests for log_dir resolution in load_config."""

from __future__ import annotations

import textwrap
from pathlib import Path

from dockyman.config import load_config


def _yaml(log_dir_line: str) -> str:
    return textwrap.dedent(f"""\
        project:
          name: test
          dockyman_version: v4.0.0
          {log_dir_line}
          swarm:
            - node_id: manager
              compose_files: [compose.yaml]
    """)


class TestLogDirResolution:
    def test_relative_path_resolved_against_config_dir(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml("log_dir: logs"))
        project = load_config(str(f))
        assert project.log_dir == str(tmp_path / "logs")

    def test_dotslash_relative_path_resolved(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml("log_dir: ./logs"))
        project = load_config(str(f))
        assert project.log_dir == str(tmp_path / "logs")

    def test_absolute_path_kept_as_is(self, tmp_path):
        abs_path = str(tmp_path / "custom" / "logs")
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml(f"log_dir: {abs_path}"))
        project = load_config(str(f))
        assert project.log_dir == abs_path

    def test_empty_string_stays_empty(self, tmp_path):
        """Empty log_dir disables all logging (no config.log, no container logs)."""
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml('log_dir: ""'))
        project = load_config(str(f))
        assert project.log_dir == ""

    def test_omitted_log_dir_defaults_to_empty(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(_yaml(""))  # no log_dir key at all
        project = load_config(str(f))
        assert project.log_dir == ""

    def test_nested_config_dir_resolves_correctly(self, tmp_path):
        sub = tmp_path / "project" / "config"
        sub.mkdir(parents=True)
        f = sub / "dockyman.yaml"
        f.write_text(_yaml("log_dir: logs"))
        project = load_config(str(f))
        assert project.log_dir == str(sub / "logs")
