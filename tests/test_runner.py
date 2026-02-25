"""Tests for dockyman.runner – SSH target extraction and RunResult."""

from __future__ import annotations

import pytest

from dockyman.config import Node
from dockyman.runner import RunResult, _ssh_target


# ── RunResult ────────────────────────────────────────────────────────────────

class TestRunResult:
    def test_ok_on_zero(self):
        assert RunResult(0, "", "").ok is True

    def test_not_ok_on_nonzero(self):
        assert RunResult(1, "", "").ok is False
        assert RunResult(127, "", "").ok is False


# ── _ssh_target ──────────────────────────────────────────────────────────────

class TestSshTarget:
    def _node(self, docker_host=None) -> Node:
        return Node(node_id="n", compose_files=["compose.yaml"], docker_host=docker_host)

    def test_none_for_local_socket(self):
        assert _ssh_target(self._node("unix:///var/run/docker.sock")) is None

    def test_none_when_no_host(self):
        assert _ssh_target(self._node(None)) is None

    def test_extracts_user_at_host(self):
        assert _ssh_target(self._node("ssh://user@hostname")) == "user@hostname"

    def test_extracts_user_at_ip(self):
        assert _ssh_target(self._node("ssh://admin@192.168.1.10")) == "admin@192.168.1.10"
