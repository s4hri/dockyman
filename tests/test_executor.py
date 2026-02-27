"""Tests for dockyman.executor – command building."""

from __future__ import annotations

import pytest

from dockyman.config import Node, Project
from dockyman.executor import _build_compose_cmd


def _make_project(
    base_dir: str = "/project",
    nodes: list[Node] | None = None,
) -> Project:
    if nodes is None:
        nodes = [Node(node_id="manager", compose_files=["compose.yaml"])]
    p = Project(name="test", dockyman_repo="https://github.com/youruser/dockyman", dockyman_ref="v4.0.0", swarm=nodes)
    p.base_dir = base_dir
    return p


# ── _build_compose_cmd ───────────────────────────────────────────────────────

class TestBuildComposeCmd:
    def test_minimal_command(self):
        project = _make_project()
        node = project.swarm[0]
        cmd = _build_compose_cmd(project, node, "up -d")
        assert "docker compose" in cmd
        assert "-f /project/compose.yaml" in cmd
        assert "up -d" in cmd

    def test_env_file_included(self):
        node = Node(node_id="n", compose_files=["compose.yaml"], env_files=[".env"])
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "up -d", command_type="run")
        assert "--env-file" in cmd
        assert ".env" in cmd

    def test_no_env_file_when_not_set(self):
        node = Node(node_id="n", compose_files=["compose.yaml"])
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "up -d")
        assert "--env-file" not in cmd

    def test_build_shell_prefix_prepended(self):
        node = Node(node_id="n", compose_files=["compose.yaml"],
                    build_shell_prefix="FOO=1")
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "build", command_type="build")
        assert cmd.startswith("FOO=1 ")

    def test_run_shell_prefix_prepended(self):
        node = Node(node_id="n", compose_files=["compose.yaml"],
                    run_shell_prefix="BAR=2")
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "up -d", command_type="run")
        assert cmd.startswith("BAR=2 ")

    def test_docker_host_in_prefix(self):
        node = Node(node_id="n", compose_files=["compose.yaml"],
                    docker_host="unix:///var/run/docker.sock")
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "up -d", command_type="run")
        assert cmd.startswith("DOCKER_HOST=unix:///var/run/docker.sock")

    def test_build_profiles_added(self):
        node = Node(node_id="n", compose_files=["compose.yaml"],
                    build_profiles=["build", "extra"])
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "build", command_type="build")
        assert "--profile build" in cmd
        assert "--profile extra" in cmd

    def test_run_extra_args_appended(self):
        node = Node(node_id="n", compose_files=["compose.yaml"],
                    run_args="--remove-orphans")
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "up -d", command_type="run")
        assert cmd.endswith("--remove-orphans")

    def test_extra_args_excluded_when_flag_false(self):
        node = Node(node_id="n", compose_files=["compose.yaml"],
                    run_args="--remove-orphans")
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "up -d", command_type="run",
                                 include_extra_args=False)
        assert "--remove-orphans" not in cmd

    def test_docker_context_included_in_path(self):
        node = Node(node_id="n", compose_files=["compose.yaml"],
                    docker_context="docker")
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "up -d")
        assert "-f /project/docker/compose.yaml" in cmd

    def test_multiple_compose_files(self):
        node = Node(node_id="n", compose_files=["compose.yaml", "compose.override.yaml"])
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "up -d")
        assert "-f /project/compose.yaml" in cmd
        assert "-f /project/compose.override.yaml" in cmd

    def test_multiple_env_files(self):
        node = Node(node_id="n", compose_files=["compose.yaml"],
                    env_files=[".env", ".env.local"])
        project = _make_project(nodes=[node])
        cmd = _build_compose_cmd(project, node, "up -d", command_type="run")
        assert "--env-file /project/.env" in cmd
        assert "--env-file /project/.env.local" in cmd
