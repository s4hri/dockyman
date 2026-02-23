"""Detect and log hardware information on each node.

Replaces the ``detect_hardware`` function from ``scripts/common.sh``.
"""

from __future__ import annotations

from .config import Node, Project
from .runner import run_on_node, command_exists_on_node
from . import logger


def _detect_node(node: Node, *, dry_run: bool = False) -> bool:
    """Gather hardware info from a single node. Returns True on success."""
    # Per-node hardware log file
    from . import config
    import os
    project = getattr(node, '_project', None)
    log_dir = getattr(project, 'log_dir', 'logs') if project else 'logs'
    node_log_dir = os.path.join(log_dir, node.node_id)
    os.makedirs(node_log_dir, exist_ok=True)
    log_path = os.path.join(node_log_dir, "config.log")
    from . import logger as _logger
    _logger.init_log(log_path)
    logger.node_header(node.node_id)

    # ── Dockyman Configuration ───────────────────────────────────────────
    if project:
        import os as _os
        compose_file = _os.path.join(project.base_dir, node.docker_context, node.compose_file)
        env_file = (
            _os.path.join(project.base_dir, node.docker_context, node.env_file)
            if node.env_file else ""
        )
        logger.section("Dockyman Configuration")
        logger.log_raw(f"compose_file   : {compose_file}")
        logger.log_raw(f"docker_host    : {node.docker_host or '(local)'}")
        if env_file:
            logger.log_raw(f"env_file       : {env_file}")
        if node.build_env_vars:
            logger.log_raw(f"build_env_vars : {node.build_env_vars}")
        if node.build_profiles:
            logger.log_raw(f"build_profiles : {', '.join(node.build_profiles)}")
        if node.build_args:
            logger.log_raw(f"build_args     : {node.build_args}")
        if node.run_env_vars:
            logger.log_raw(f"run_env_vars   : {node.run_env_vars}")
        if node.run_profiles:
            logger.log_raw(f"run_profiles   : {', '.join(node.run_profiles)}")
        if node.run_args:
            logger.log_raw(f"run_args       : {node.run_args}")
        if node.display:
            logger.log_raw(f"display        : {node.display}")
        if node.display_args:
            logger.log_raw(f"display_args   : {node.display_args}")
        if node.audio_volume is not None:
            logger.log_raw(f"audio_volume   : {node.audio_volume}%")
        if node.audio_card:
            logger.log_raw(f"audio_card     : {node.audio_card}")
        if node.audio_input_volume is not None:
            logger.log_raw(f"audio_in_vol   : {node.audio_input_volume}%")
        if node.audio_input_card:
            logger.log_raw(f"audio_in_card  : {node.audio_input_card}")

    # ── System / OS ──────────────────────────────────────────────────────
    logger.section("System Information")
    res = run_on_node(node, "hostnamectl 2>/dev/null || hostname", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)
    res = run_on_node(node, "cat /etc/os-release 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)
    res = run_on_node(node, "uname -a", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)

    # ── CPU ──────────────────────────────────────────────────────────────
    logger.section("CPU")
    res = run_on_node(node, "lscpu 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)

    # ── Memory ───────────────────────────────────────────────────────────
    logger.section("Memory")
    res = run_on_node(node, "free -h", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)

    # ── GPU / Graphics ─────────────────────────────────────────────────--
    logger.section("Graphics / GPU")
    res = run_on_node(node, "lspci 2>/dev/null | grep -i -E 'vga|3d|display'", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)
    res = run_on_node(node, "nvidia-smi -L 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)
    res = run_on_node(node, "xrandr --query 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)

    # (Display info now included above)

    # ── Audio Cards ─────────────────────────────────────────────────-----
    logger.section("Audio Cards")
    res = run_on_node(node, "pactl list short sinks 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)
    res = run_on_node(node, "aplay -l 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)

    # ── Audio Input Devices ─────────────────────────────────────────-----
    logger.section("Audio Input Devices")
    res = run_on_node(node, "pactl list short sources 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)
    res = run_on_node(node, "arecord -l 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)

    # ── USB Devices ─────────────────────────────────────────────────-----
    logger.section("USB Devices")
    res = run_on_node(node, "lsusb 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)

    # ── Network Cards ─────────────────────────────────────────────────---
    logger.section("Network Cards")
    res = run_on_node(node, "ip -br addr 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)

    # ── Disks ─────────────────────────────────────────────────────────---
    logger.section("Disks")
    res = run_on_node(node, "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL 2>/dev/null", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)
    res = run_on_node(node, "df -h", capture=True, dry_run=dry_run)
    if res.ok and res.stdout:
        logger.log_raw(res.stdout)

    if not logger._quiet:
        print()
    return True


def detect_hardware(project: Project, *, dry_run: bool = False) -> bool:
    """Detect hardware on all nodes in the swarm."""
    logger.header(f"Hardware information for project '{project.name}'")
    all_ok = True
    for node in project.swarm:
        # Attach project to node for log_dir access
        node._project = project
        if not _detect_node(node, dry_run=dry_run):
            all_ok = False
    return all_ok


# ── Setup (display + audio from yaml config) ────────────────────────────────


def setup(project: Project, *, dry_run: bool = False) -> bool:
    """Apply per-node display and audio settings from *dockyman.yaml*.

    Reads ``display_args``, ``audio_volume``, ``audio_card``,
    ``audio_input_volume``, and ``audio_input_card`` from each node.
    Failures are logged but do not abort the remaining nodes.
    """
    from .display import _apply_display_node
    from .audio import _set_volume_node, _set_input_volume_node

    logger.header(f"Hardware setup for project '{project.name}'")
    all_ok = True

    for node in project.swarm:
        # Attach project to node for log_dir access
        node._project = project
        # Per-node hardware log file
        from . import logger as _logger
        import os
        log_dir = project.log_dir or 'logs'
        node_log_dir = os.path.join(log_dir, node.node_id)
        os.makedirs(node_log_dir, exist_ok=True)
        log_path = os.path.join(node_log_dir, "config.log")
        _logger.init_log(log_path)

        # Log full hardware info at the start
        _detect_node(node, dry_run=dry_run)

        # Display
        if not _apply_display_node(node, None, dry_run=dry_run):
            all_ok = False

        # Audio output
        if node.audio_volume is not None:
            if not _set_volume_node(node, node.audio_volume, None, dry_run=dry_run):
                all_ok = False

        # Audio input
        if node.audio_input_volume is not None:
            if not _set_input_volume_node(node, node.audio_input_volume, None, dry_run=dry_run):
                all_ok = False

    return all_ok
