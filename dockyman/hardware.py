"""Detect and log hardware information on each node.

Replaces the ``detect_hardware`` function from ``scripts/common.sh``.
"""

from __future__ import annotations

import os

from .config import Node, Project
from .runner import run_on_node
from .ansible import run_playbooks
from . import logger


def _detect_node(node: Node, *, dry_run: bool = False, to_stdout: bool = False) -> bool:
    """Gather hardware info from a single node. Returns True on success.

    When *to_stdout* is True the command output is streamed live to the
    console (used when no ``log_dir`` is configured).  When False the output
    is captured silently and written to the log file.

    Assumes the log file has already been initialised by the caller.
    """
    project = getattr(node, '_project', None)

    def _section(title: str) -> None:
        if to_stdout:
            print(f"\n{logger.BOLD}  ─── {title} ───{logger.RESET}")
        else:
            logger.section(title)

    def _section_always(title: str) -> None:
        """Print section header to console AND log, regardless of to_stdout."""
        if not logger._quiet:
            print(f"\n{logger.BOLD}  ─── {title} ───{logger.RESET}")
        logger.section(title)

    def _raw(text: str) -> None:
        if to_stdout:
            for line in text.splitlines():
                print(f"  {line}")
        else:
            logger.log_raw(text)

    def _info(text: str) -> None:
        """Print to console AND log, regardless of to_stdout."""
        if not logger._quiet:
            for line in text.splitlines():
                print(f"  {line}")
        logger.log_raw(text)

    def _run(cmd: str) -> None:
        if to_stdout:
            run_on_node(node, cmd, capture=False, echo=True, dry_run=dry_run)
        else:
            res = run_on_node(node, cmd, capture=True, echo=False, dry_run=dry_run)
            if res.ok and res.stdout:
                logger.log_raw(res.stdout)

    # ── Dockyman Configuration ───────────────────────────────────────────
    if project:
        compose_files = [
            os.path.join(project.base_dir, node.docker_context, cf)
            for cf in node.compose_files
        ]
        env_files = [
            os.path.join(project.base_dir, node.docker_context, ef)
            for ef in node.env_files
        ]
        _section_always("Dockyman Configuration")
        for cf in compose_files:
            _info(f"compose_file   : {cf}")
        _info(f"docker_host    : {node.docker_host or '(local)'}")
        for ef in env_files:
            _info(f"env_file       : {ef}")
        if node.build_shell_prefix:
            _info(f"build_shell_prefix : {node.build_shell_prefix}")
        if node.build_profiles:
            _info(f"build_profiles     : {', '.join(node.build_profiles)}")
        if node.build_args:
            _info(f"build_args         : {node.build_args}")
        if node.run_shell_prefix:
            _info(f"run_shell_prefix   : {node.run_shell_prefix}")
        if node.run_profiles:
            _info(f"run_profiles   : {', '.join(node.run_profiles)}")
        if node.run_args:
            _info(f"run_args       : {node.run_args}")

    # ── System / OS ──────────────────────────────────────────────────────
    _section("System Information")
    _run("hostnamectl 2>/dev/null || hostname")
    _run("cat /etc/os-release 2>/dev/null")
    _run("uname -a")

    # ── CPU ──────────────────────────────────────────────────────────────
    _section("CPU")
    _run("lscpu 2>/dev/null")

    # ── Memory ───────────────────────────────────────────────────────────
    _section("Memory")
    _run("free -h")

    # ── GPU / Graphics ───────────────────────────────────────────────────
    _section("Graphics / GPU")
    _run("lspci 2>/dev/null | grep -i -E 'vga|3d|display'")
    _run("nvidia-smi -L 2>/dev/null")
    _run("xrandr --query 2>/dev/null")

    # ── Audio Cards ──────────────────────────────────────────────────────
    _section("Audio Cards")
    _run("pactl list short sinks 2>/dev/null")
    _run("aplay -l 2>/dev/null")

    # ── Audio Input Devices ──────────────────────────────────────────────
    _section("Audio Input Devices")
    _run("pactl list short sources 2>/dev/null")
    _run("arecord -l 2>/dev/null")

    # ── USB Devices ──────────────────────────────────────────────────────
    _section("USB Devices")
    _run("lsusb 2>/dev/null")

    # ── Network Cards ────────────────────────────────────────────────────
    _section("Network Cards")
    _run("ip -br addr 2>/dev/null")

    # ── Disks ────────────────────────────────────────────────────────────
    _section("Disks")
    _run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL 2>/dev/null")
    _run("df -h")

    if not logger._quiet:
        print()
    return True


def detect_hardware(project: Project, *, dry_run: bool = False,
                    _init_log: bool = True, _show_header: bool = True) -> bool:
    """Detect hardware on all nodes in the swarm.

    Output destination depends on ``project.config_log_dir``:

    - Set     → config section printed to console; hardware scan captured to
                ``<node_id>.log`` silently.
    - Not set → everything streamed live to stdout.

    *_show_header*: set False to suppress the "Hardware information" banner
    (e.g. when called from ``dockyman run``).
    """
    if _show_header:
        logger.header(f"Hardware information for project '{project.name}'")
    all_ok = True
    for node in project.nodes:
        if project.config_log_dir:
            os.makedirs(project.config_log_dir, exist_ok=True)
            log_path = os.path.join(project.config_log_dir, f"{node.node_id}.log")
            logger.init_log(log_path)
            logger.saved(log_path)
        logger.node_header(node.node_id)
        if not _detect_node(node, dry_run=dry_run, to_stdout=not project.config_log_dir):
            all_ok = False
    return all_ok


# ── Setup ───────────────────────────────────────────────────────────────────


def setup(project: Project, *, dry_run: bool = False) -> bool:
    """Run Ansible playbooks for the setup hook on every node.

    Playbooks whose ``hook`` is ``"setup"`` (or whose hook is unset, since
    setup is the default phase) are executed in declaration order.
    """
    logger.header(f"Hardware setup for project '{project.name}'")

    ok = run_playbooks(project, hook="setup", dry_run=dry_run)
    return ok
