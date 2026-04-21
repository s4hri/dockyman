"""Tests for dockyman.config – config parsing and Node helpers."""

from __future__ import annotations

import textwrap
import pytest

from jinja2 import exceptions as jinja2_exceptions

from dockyman.config import Node, Project, load_config, render_config

# ── Node.get_env_prefix ──────────────────────────────────────────────────────

class TestGetEnvPrefix:
    def _node(self, **kwargs) -> Node:
        return Node(node_id="n", compose_files=["compose.yaml"], **kwargs)

    def test_empty_by_default(self):
        assert self._node().get_env_prefix() == ""

    def test_docker_host_always_included(self):
        n = self._node(docker_host="unix:///var/run/docker.sock")
        assert n.get_env_prefix() == "DOCKER_HOST=unix:///var/run/docker.sock"
        assert n.get_env_prefix("build") == "DOCKER_HOST=unix:///var/run/docker.sock"
        assert n.get_env_prefix("run") == "DOCKER_HOST=unix:///var/run/docker.sock"

    def test_build_shell_prefix_only_for_build(self):
        n = self._node(build_shell_prefix="FOO=1")
        assert n.get_env_prefix("build") == "FOO=1"
        assert n.get_env_prefix("run") == ""
        assert n.get_env_prefix() == ""

    def test_run_shell_prefix_only_for_run(self):
        n = self._node(run_shell_prefix="BAR=2")
        assert n.get_env_prefix("run") == "BAR=2"
        assert n.get_env_prefix("build") == ""

    def test_docker_host_and_shell_prefix_combined(self):
        n = self._node(
            docker_host="ssh://user@host",
            run_shell_prefix="PUID=1000 PGID=1000",
        )
        result = n.get_env_prefix("run")
        assert result == "DOCKER_HOST=ssh://user@host PUID=1000 PGID=1000"

    def test_whitespace_only_prefix_ignored(self):
        n = self._node(build_shell_prefix="   ")
        assert n.get_env_prefix("build") == ""


# ── Node.is_remote ───────────────────────────────────────────────────────────

class TestIsRemote:
    def _node(self, docker_host=None) -> Node:
        return Node(node_id="n", compose_files=["compose.yaml"], docker_host=docker_host)

    def test_local_socket_is_not_remote(self):
        assert not self._node("unix:///var/run/docker.sock").is_remote

    def test_ssh_host_is_remote(self):
        assert self._node("ssh://user@hostname").is_remote

    def test_none_is_not_remote(self):
        assert not self._node(None).is_remote


# ── load_config ──────────────────────────────────────────────────────────────

class TestLoadConfig:
    MINIMAL_YAML = textwrap.dedent("""\
        project:
          name: test_project
          dockyman_repo: https://github.com/s4hri/dockyman
          dockyman_ref: v4.0.0
          swarm:
            - node_id: manager
              compose_files: [compose.yaml]
    """)

    FULL_YAML = textwrap.dedent("""\
        project:
          name: full_project
          dockyman_repo: https://github.com/s4hri/dockyman
          dockyman_ref: v4.0.0
          log_dir: logs
          swarm:
            - node_id: local
              compose_files: [compose.yaml]
              docker_context: docker
              docker_host: unix:///var/run/docker.sock
              env_files: [.env]
              build_shell_prefix: "PUID=1000"
              build_profiles: [build]
              build_args: "--no-cache"
              run_shell_prefix: "PUID=1000"
              run_profiles: [prod]
              run_args: "--remove-orphans"
              setup_script: "xrandr --auto"
            - node_id: remote
              compose_files: [compose.yaml]
              docker_host: ssh://user@remotehost
    """)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(str(tmp_path / "nonexistent.yaml"))

    def test_minimal_config_loads(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(self.MINIMAL_YAML)
        project = load_config(str(f))
        assert project.name == "test_project"
        assert project.dockyman_repo == "https://github.com/s4hri/dockyman"
        assert project.dockyman_ref == "v4.0.0"
        assert len(project.swarm) == 1
        assert project.swarm[0].node_id == "manager"

    def test_base_dir_is_resolved(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(self.MINIMAL_YAML)
        project = load_config(str(f))
        assert project.base_dir == str(tmp_path.resolve())

    def test_full_config_loads_all_fields(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(self.FULL_YAML)
        project = load_config(str(f))

        # Old log_dir backward-compat: should set both directories
        assert project.container_log_dir == str(tmp_path / "logs")
        assert project.config_log_dir == str(tmp_path / "logs")
        assert len(project.swarm) == 2

        local = project.swarm[0]
        assert local.node_id == "local"
        assert local.docker_context == "docker"
        assert local.docker_host == "unix:///var/run/docker.sock"
        assert local.env_files == [".env"]
        assert local.build_shell_prefix == "PUID=1000"
        assert local.build_profiles == ["build"]
        assert local.build_args == "--no-cache"
        assert local.run_shell_prefix == "PUID=1000"
        assert local.run_profiles == ["prod"]
        assert local.run_args == "--remove-orphans"
        assert local.setup_script.strip() == "xrandr --auto"

        remote = project.swarm[1]
        assert remote.node_id == "remote"
        assert remote.docker_host == "ssh://user@remotehost"
        assert remote.is_remote

    def test_optional_fields_default_to_empty(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(self.MINIMAL_YAML)
        node = load_config(str(f)).swarm[0]
        assert node.docker_context == ""
        assert node.docker_host is None
        assert node.env_files == []
        assert node.build_shell_prefix == ""
        assert node.build_profiles == []
        assert node.build_args == ""
        assert node.run_shell_prefix == ""
        assert node.run_profiles == []
        assert node.run_args == ""
        assert node.setup_script == ""

    def test_backward_compat_single_compose_file(self, tmp_path):
        """Old ``compose_file: name.yaml`` (without s) still loads correctly."""
        yaml_text = textwrap.dedent("""\
            project:
              name: compat
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              swarm:
                - node_id: manager
                  compose_file: old.yaml
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        assert load_config(str(f)).swarm[0].compose_files == ["old.yaml"]

    def test_backward_compat_single_env_file(self, tmp_path):
        """Old ``env_file: .env`` (without s) still loads correctly."""
        yaml_text = textwrap.dedent("""\
            project:
              name: compat
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              swarm:
                - node_id: manager
                  compose_files: [compose.yaml]
                  env_file: .env
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        assert load_config(str(f)).swarm[0].env_files == [".env"]

    def test_multiple_compose_files_loaded(self, tmp_path):
        """Multiple compose files are loaded as a list."""
        yaml_text = textwrap.dedent("""\
            project:
              name: multi
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              swarm:
                - node_id: manager
                  compose_files:
                    - compose.yaml
                    - compose.override.yaml
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        assert load_config(str(f)).swarm[0].compose_files == ["compose.yaml", "compose.override.yaml"]

    def test_multiple_env_files_loaded(self, tmp_path):
        """Multiple env files are loaded as a list."""
        yaml_text = textwrap.dedent("""\
            project:
              name: multi
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              swarm:
                - node_id: manager
                  compose_files: [compose.yaml]
                  env_files:
                    - .env
                    - .env.local
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        assert load_config(str(f)).swarm[0].env_files == [".env", ".env.local"]

    def test_render_config(self, tmp_path):
        """Test jinja vars rendering."""

        jinja_vars_text = textwrap.dedent("""\
        {% set project_name = "test_name" %}
        {% set manager_node_id = "test_manager" %}
        """)
        f = tmp_path / "vars.j2"
        f.write_text(jinja_vars_text)

        yaml_j2_text = textwrap.dedent("""\
            {% import "vars.j2" as vars %}
            project:
              name: {{ vars.project_name }}
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              swarm:
                - node_id: {{ vars.manager_node_id }}
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml.j2"
        f.write_text(yaml_j2_text)

        project = load_config(str(f))
        assert project.name == "test_name"
        assert project.swarm[0].node_id == "test_manager"

    def test_render_config_missing_var(self, tmp_path):
        """Test jinja rendering failure when a var is not defined."""

        # we do not define {% set manager_node_id = "test_manager" %}
        # we expect to get an exception 
        jinja_vars_text = textwrap.dedent("""\
        {% set project_name = "test_name" %}
        """)
        f = tmp_path / "vars.j2"
        f.write_text(jinja_vars_text)

        yaml_j2_text = textwrap.dedent("""\
            {% import "vars.j2" as vars %}
            project:
              name: {{ vars.project_name }}
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              swarm:
                - node_id: {{ vars.manager_node_id }}
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml.j2"
        f.write_text(yaml_j2_text)

        with pytest.raises(jinja2_exceptions.UndefinedError) as exc_info:
            render_config(str(f))

        # verify the error message points only to the missing variable
        assert not("no attribute 'project_name'" in str(exc_info.value))
        assert "no attribute 'manager_node_id'" in str(exc_info.value)
