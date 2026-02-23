"""Display detection and xrandr configuration on each node.

Replaces ``scripts/setup_display.sh``.
"""

from __future__ import annotations

from typing import Optional

from .config import Node, Project
from .runner import run_on_node
from . import logger


# ── Listing ──────────────────────────────────────────────────────────────────


def list_displays(project: Project, *, node_id: Optional[str] = None, dry_run: bool = False) -> bool:
    """List connected displays on matching nodes."""
    logger.header(f"Displays for project '{project.name}'")
    nodes = _filter_nodes(project, node_id)
    all_ok = True
    for node in nodes:
        logger.node_header(node.node_id)
        res = run_on_node(
            node,
            'xrandr 2>/dev/null | grep -E "^[A-Za-z0-9-]+ (connected|disconnected)"',
            capture=True, dry_run=dry_run,
        )
        if res.ok and res.stdout:
            for line in res.stdout.splitlines():
                logger.info(line)
            logger.log_raw(res.stdout)
        else:
            logger.warn("xrandr not available or DISPLAY not set")
            all_ok = False
        print()
    return all_ok


# ── Auto-detect ──────────────────────────────────────────────────────────────


def _display_prefix(node: Node) -> str:
    """Return an ``export DISPLAY=...;`` prefix when needed (remote nodes)."""
    if node.display:
        return f"export DISPLAY={node.display}; "
    return ""


def _auto_detect_xrandr(node: Node, *, dry_run: bool = False) -> Optional[str]:
    """Return auto-detected xrandr args (``--output <name> --mode <WxH>``)."""
    # Try primary display first, then first connected
    script = (
        f"{_display_prefix(node)}"
        "output=$(xrandr 2>/dev/null | grep ' connected primary' | cut -d' ' -f1); "
        "[ -z \"$output\" ] && output=$(xrandr 2>/dev/null | grep ' connected' | head -n1 | cut -d' ' -f1); "
        "[ -z \"$output\" ] && exit 1; "
        "mode=$(xrandr 2>/dev/null | grep -A 50 \"^${output}\" "
        "| grep -E '^\\s+[0-9]+x[0-9]+' | grep -E '\\+|\\*' | head -n1 | awk '{print $1}'); "
        "[ -z \"$mode\" ] && mode=$(xrandr 2>/dev/null | grep -A 50 \"^${output}\" "
        "| grep -E '^\\s+[0-9]+x[0-9]+' | head -n1 | awk '{print $1}'); "
        "echo \"--output $output --mode $mode\""
    )
    res = run_on_node(node, script, capture=True, dry_run=dry_run)
    if res.ok and res.stdout and "--output" in res.stdout:
        return res.stdout.strip()
    return None


# ── Apply ────────────────────────────────────────────────────────────────────


def _apply_display_node(
    node: Node, xrandr_args: Optional[str], *, dry_run: bool = False,
) -> bool:
    logger.node_header(node.node_id)

    # Check DISPLAY
    dp = _display_prefix(node)
    res = run_on_node(node, f"{dp}echo $DISPLAY", capture=True, dry_run=dry_run)
    if not dry_run and (not res.ok or not res.stdout):
        logger.warn("DISPLAY not set – skipping display configuration")
        print()
        return True  # not a failure, just nothing to do

    # CLI override → node yaml → auto-detect
    args = xrandr_args or node.display_args or None
    if not args:
        logger.info("Auto-detecting display configuration…")
        args = _auto_detect_xrandr(node, dry_run=dry_run)
        if not args:
            logger.warn("Could not auto-detect display configuration")
            print()
            return True

    logger.info(f"Applying: xrandr {args}")
    res = run_on_node(node, f"{dp}xrandr {args}", dry_run=dry_run)
    if res.ok:
        logger.ok("Display configuration applied")
        logger.section("Display Configuration Applied")
        run_on_node(node, f"{dp}xrandr --query", capture=True, dry_run=dry_run)
    else:
        logger.fail("Failed to apply display configuration")
        run_on_node(node, f"{dp}xrandr --query", dry_run=dry_run)
        print()
        return False
    print()
    return True


def apply_display(
    project: Project, xrandr_args: Optional[str] = None,
    *, node_id: Optional[str] = None, dry_run: bool = False,
) -> bool:
    """Apply display configuration on matching nodes.

    If *xrandr_args* is ``None``, auto-detects the primary display at its
    preferred resolution.
    """
    logger.header(f"Display configuration for project '{project.name}'")
    nodes = _filter_nodes(project, node_id)
    return all(_apply_display_node(n, xrandr_args, dry_run=dry_run) for n in nodes)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _filter_nodes(project: Project, node_id: Optional[str]) -> list[Node]:
    if node_id:
        return [n for n in project.swarm if n.node_id == node_id]
    return project.swarm
