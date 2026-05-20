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
          nodes:
            manager:
              compose_files: [compose.yaml]
    """)

    FULL_YAML = textwrap.dedent("""\
        project:
          name: full_project
          dockyman_repo: https://github.com/s4hri/dockyman
          dockyman_ref: v4.0.0
          log_dir: logs
          nodes:
            local:
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
            remote:
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
        assert len(project.nodes) == 1
        assert project.nodes[0].node_id == "manager"

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
        assert len(project.nodes) == 2

        local = project.nodes[0]
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

        remote = project.nodes[1]
        assert remote.node_id == "remote"
        assert remote.docker_host == "ssh://user@remotehost"
        assert remote.is_remote

    def test_optional_fields_default_to_empty(self, tmp_path):
        f = tmp_path / "dockyman.yaml"
        f.write_text(self.MINIMAL_YAML)
        node = load_config(str(f)).nodes[0]
        assert node.docker_context == ""
        assert node.docker_host is None
        assert node.env_files == []
        assert node.build_shell_prefix == ""
        assert node.build_profiles == []
        assert node.build_args == ""
        assert node.run_shell_prefix == ""
        assert node.run_profiles == []
        assert node.run_args == ""

    def test_global_profiles_inherited_by_nodes(self, tmp_path):
        """Nodes without explicit profiles inherit project-level defaults."""
        yaml_text = textwrap.dedent("""\
            project:
              name: global_prof
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              build_profiles: [build]
              run_profiles: [production]
              pull_profiles: [production]
              push_profiles: [push]
              nodes:
                nodeA:
                  compose_files: [compose.yaml]
                nodeB:
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        for node in project.nodes:
            assert node.build_profiles == ["build"]
            assert node.run_profiles == ["production"]
            assert node.pull_profiles == ["production"]
            assert node.push_profiles == ["push"]

    def test_node_profiles_override_global(self, tmp_path):
        """Explicit node-level profiles override the project defaults."""
        yaml_text = textwrap.dedent("""\
            project:
              name: override_prof
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              build_profiles: [build]
              run_profiles: [production]
              nodes:
                nodeA:
                  compose_files: [compose.yaml]
                nodeB:
                  compose_files: [compose.yaml]
                  build_profiles: [custom-build]
                  run_profiles: []
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        # nodeA inherits global defaults
        assert project.nodes[0].build_profiles == ["build"]
        assert project.nodes[0].run_profiles == ["production"]
        # nodeB overrides both
        assert project.nodes[1].build_profiles == ["custom-build"]
        assert project.nodes[1].run_profiles == []

    def test_backward_compat_swarm_key(self, tmp_path):
        """Old ``swarm:`` list form still loads correctly as ``nodes``."""
        yaml_text = textwrap.dedent("""\
            project:
              name: compat
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              swarm:
                - node_id: manager
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        assert len(project.nodes) == 1
        assert project.nodes[0].node_id == "manager"

    def test_backward_compat_nodes_list(self, tmp_path):
        """Old ``nodes:`` list form with explicit ``node_id`` still loads."""
        yaml_text = textwrap.dedent("""\
            project:
              name: compat
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              nodes:
                - node_id: manager
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        assert len(project.nodes) == 1
        assert project.nodes[0].node_id == "manager"

    def test_project_level_playbooks(self, tmp_path):
        """project.playbooks: are parsed as project-scoped entries."""
        yaml_text = textwrap.dedent("""\
            project:
              name: pb_test
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              inventory: ./inventory/hosts.yaml
              playbooks:
                - name: setup_all
                  file: ./ansible/setup.yaml
                  hook: before_run
                  extra_vars:
                    foo: bar
                - name: teardown
                  file: ./ansible/teardown.yaml
              nodes:
                manager:
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        assert len(project.project_playbooks) == 2
        pb = project.project_playbooks[0]
        assert pb.name == "setup_all"
        assert pb.file == "./ansible/setup.yaml"
        assert pb.hook == "before_run"
        assert pb.extra_vars == {"foo": "bar"}
        assert pb.project_scope is True
        assert pb.nodes == []
        pb2 = project.project_playbooks[1]
        assert pb2.hook == ""
        assert pb2.project_scope is True

    def test_vars_file_loaded_into_project(self, tmp_path):
        """``project.vars_files`` is populated from the YAML (scalar form)."""
        yaml_text = textwrap.dedent("""\
            project:
              name: inv_test
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              vars_file: ./inventory/hosts.yaml
              nodes:
                manager:
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        assert project.vars_files == ["./inventory/hosts.yaml"]

    def test_vars_files_list_loaded_into_project(self, tmp_path):
        """``project.vars_files`` is populated from the YAML (list form)."""
        yaml_text = textwrap.dedent("""\
            project:
              name: inv_test
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              vars_file:
                - ./vars/base.yaml
                - ./vars/hosts.yaml
              nodes:
                manager:
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        assert project.vars_files == ["./vars/base.yaml", "./vars/hosts.yaml"]

    def test_generic_vars_file_exposed_as_template_globals(self, tmp_path):
        """Any YAML file's top-level keys are available as Jinja2 globals."""
        vars_file = tmp_path / "myvars.yaml"
        vars_file.write_text(textwrap.dedent("""\
            db:
              host: 192.168.1.10
              port: 5432
            version: "1.2.3"
        """))
        yaml_text = textwrap.dedent("""\
            project:
              name: test_project
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              vars_file: myvars.yaml
              vars:
                db_host: "{{ db.host }}"
                app_version: "{{ version }}"
              nodes:
                manager:
                  compose_files: [compose.yaml]
                  docker_host: "{{ db_host }}"
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        assert project.nodes[0].docker_host == "192.168.1.10"

    def test_inventory_backward_compat(self, tmp_path):
        """Old ``inventory:`` key still populates ``vars_files``."""
        yaml_text = textwrap.dedent("""\
            project:
              name: inv_test
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              inventory: ./ansible/inventory.yaml
              nodes:
                manager:
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        assert project.vars_files == ["./ansible/inventory.yaml"]

    def test_backward_compat_single_compose_file(self, tmp_path):
        """Old ``compose_file: name.yaml`` (without s) still loads correctly."""
        yaml_text = textwrap.dedent("""\
            project:
              name: compat
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              nodes:
                manager:
                  compose_file: old.yaml
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        assert load_config(str(f)).nodes[0].compose_files == ["old.yaml"]

    def test_backward_compat_single_env_file(self, tmp_path):
        """Old ``env_file: .env`` (without s) still loads correctly."""
        yaml_text = textwrap.dedent("""\
            project:
              name: compat
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              nodes:
                manager:
                  compose_files: [compose.yaml]
                  env_file: .env
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        assert load_config(str(f)).nodes[0].env_files == [".env"]

    def test_multiple_compose_files_loaded(self, tmp_path):
        """Multiple compose files are loaded as a list."""
        yaml_text = textwrap.dedent("""\
            project:
              name: multi
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              nodes:
                manager:
                  compose_files:
                    - compose.yaml
                    - compose.override.yaml
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        assert load_config(str(f)).nodes[0].compose_files == ["compose.yaml", "compose.override.yaml"]

    def test_multiple_env_files_loaded(self, tmp_path):
        """Multiple env files are loaded as a list."""
        yaml_text = textwrap.dedent("""\
            project:
              name: multi
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              nodes:
                manager:
                  compose_files: [compose.yaml]
                  env_files:
                    - .env
                    - .env.local
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        assert load_config(str(f)).nodes[0].env_files == [".env", ".env.local"]

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
              nodes:
                {{ vars.manager_node_id }}:
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_j2_text)

        project = load_config(str(f))
        assert project.name == "test_name"
        assert project.nodes[0].node_id == "test_manager"

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
              nodes:
                {{ vars.manager_node_id }}:
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_j2_text)

        with pytest.raises(jinja2_exceptions.UndefinedError) as exc_info:
            render_config(str(f))

        # verify the error message points only to the missing variable
        assert not("no attribute 'project_name'" in str(exc_info.value))
        assert "no attribute 'manager_node_id'" in str(exc_info.value)


# ── Node-level playbooks ─────────────────────────────────────────────────────

class TestNodePlaybooks:
    def test_node_playbooks_parsed(self, tmp_path):
        """Playbooks nested under a node are parsed with implicit node limit."""
        yaml_text = textwrap.dedent("""\
            project:
              name: test_project
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              nodes:
                manager:
                  compose_files: [compose.yaml]
                  playbooks:
                    - name: configure_audio
                      file: ./playbooks/configure_audio.yaml
                      hook: before_run
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        node = project.nodes[0]
        assert len(node.playbooks) == 1
        pb = node.playbooks[0]
        assert pb.name == "configure_audio"
        assert pb.file == "./playbooks/configure_audio.yaml"
        assert pb.hook == "before_run"
        assert pb.nodes == ["manager"]

    def test_node_playbook_extra_vars(self, tmp_path):
        """extra_vars on a node playbook are parsed into a dict."""
        yaml_text = textwrap.dedent("""\
            project:
              name: test_project
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              nodes:
                manager:
                  compose_files: [compose.yaml]
                  playbooks:
                    - name: configure_audio
                      file: ./playbooks/configure_audio.yaml
                      hook: before_run
                      extra_vars:
                        volume: "75%"
                        brightness: "80%"
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        pb = project.nodes[0].playbooks[0]
        assert pb.extra_vars == {"volume": "75%", "brightness": "80%"}

    def test_node_playbooks_default_empty(self, tmp_path):
        """Nodes without a playbooks: section have an empty list."""
        yaml_text = textwrap.dedent("""\
            project:
              name: test_project
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              nodes:
                manager:
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        assert project.nodes[0].playbooks == []

    def test_multiple_nodes_independent_playbooks(self, tmp_path):
        """Each node carries only its own playbooks."""
        yaml_text = textwrap.dedent("""\
            project:
              name: test_project
              dockyman_repo: https://github.com/s4hri/dockyman
              dockyman_ref: v4.0.0
              nodes:
                manager:
                  compose_files: [compose.yaml]
                  playbooks:
                    - name: configure_audio
                      file: ./playbooks/configure_audio.yaml
                worker:
                  compose_files: [compose.yaml]
        """)
        f = tmp_path / "dockyman.yaml"
        f.write_text(yaml_text)
        project = load_config(str(f))
        assert len(project.nodes[0].playbooks) == 1
        assert project.nodes[0].playbooks[0].nodes == ["manager"]
        assert project.nodes[1].playbooks == []
