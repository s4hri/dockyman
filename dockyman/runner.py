"""Run shell commands on local or remote nodes transparently."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Optional

from .config import Node
from . import logger


@dataclass
class RunResult:
    """Captures the result of a command execution."""
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _ssh_target(node: Node) -> Optional[str]:
    """Extract ``user@host`` from an ``ssh://user@host`` DOCKER_HOST.

    Returns *None* for local nodes.
    """
    host = node.docker_host
    if host and host.startswith("ssh://"):
        return host.removeprefix("ssh://")
    return None


def run_on_node(
    node: Node,
    cmd: str,
    *,
    capture: bool = False,
    dry_run: bool = False,
) -> RunResult:
    """Execute *cmd* on the given node.

    * **Local nodes** – the command runs in a local shell.
    * **Remote nodes** (``ssh://``) – the command is wrapped in
      ``ssh user@host '<cmd>'``.

    If *capture* is True the output is captured instead of streamed to the
    terminal.

    Returns a :class:`RunResult`.
    """
    ssh_target = _ssh_target(node)
    if ssh_target:
        # Escape single quotes for safe SSH transport: ' → '\''
        escaped = cmd.replace("'", "'\\''")
        full_cmd = f"ssh {ssh_target} '{escaped}'"
    else:
        full_cmd = cmd

    if dry_run:
        if not logger._quiet:
            print(f"  {logger.YELLOW}[dry-run]{logger.RESET} {full_cmd}")
        return RunResult(0, "", "")

    if not logger._quiet:
        print(f"  {logger.BOLD}${logger.RESET} {full_cmd}")

    if capture:
        result = subprocess.run(
            full_cmd, shell=True, capture_output=True, text=True,
        )
        return RunResult(result.returncode, result.stdout.strip(), result.stderr.strip())
    else:
        result = subprocess.run(full_cmd, shell=True)
        return RunResult(result.returncode, "", "")


def command_exists_on_node(
    node: Node, command: str, *, dry_run: bool = False,
) -> bool:
    """Check whether *command* is available on *node*."""
    res = run_on_node(node, f"command -v {command}", capture=True, dry_run=dry_run)
    return res.ok
