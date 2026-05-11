"""Run Ansible playbooks defined in dockyman.yaml."""

from __future__ import annotations

import subprocess
from typing import Optional

from .config import AnsibleConfig, AnsiblePlaybook, Project
from . import logger


def _run_playbook(playbook: AnsiblePlaybook, inventory: str,
                  node_filter: Optional[str] = None,
                  dry_run: bool = False) -> int:
    """Execute a single ansible-playbook command.

    Returns the process exit code (0 = success).
    """
    # Resolve target: explicit CLI --node overrides the playbook's own nodes list
    if node_filter:
        limit = node_filter
    elif playbook.nodes and playbook.nodes != ["all"]:
        limit = ",".join(playbook.nodes)
    else:
        limit = None

    cmd_parts = ["ansible-playbook", "-i", inventory, playbook.file]
    if limit:
        cmd_parts += ["--limit", limit]

    cmd_str = " ".join(cmd_parts)

    if dry_run:
        print(f"  {logger.YELLOW}[dry-run]{logger.RESET} {cmd_str}")
        return 0

    print(f"  {logger.BOLD}${logger.RESET} {cmd_str}")
    result = subprocess.run(cmd_parts)
    return result.returncode


def run_playbooks(project: Project,
                  playbook_filter: Optional[str] = None,
                  node_filter: Optional[str] = None,
                  hook: Optional[str] = None,
                  dry_run: bool = False) -> bool:
    """Run Ansible playbooks declared in the project.

    Args:
        playbook_filter: When given, only run the playbook with this name.
        node_filter:     When given, pass ``--limit <node>`` to ansible-playbook.
        hook:            When given, only run playbooks whose ``hook`` matches.
                         When None (explicit ``dockyman ansible`` command), run
                         all playbooks regardless of their hook value.
        dry_run:         Print commands without executing them.

    Returns True if all playbooks succeeded (or there were none to run).
    """
    if project.ansible is None:
        logger.warn("No 'ansible' section found in dockyman.yaml — nothing to run.")
        return True

    cfg: AnsibleConfig = project.ansible
    playbooks = cfg.playbooks

    # Filter by name if requested
    if playbook_filter:
        playbooks = [p for p in playbooks if p.name == playbook_filter]
        if not playbooks:
            import sys as _sys
            print(f"Error: no playbook named '{playbook_filter}'", file=_sys.stderr)
            return False

    # Filter by lifecycle hook (None = run all)
    if hook is not None:
        playbooks = [p for p in playbooks if p.hook == hook]

    if not playbooks:
        return True

    label = f"hook '{hook}'" if hook else "playbooks"
    logger.header(f"Running Ansible {label} for project '{project.name}' ...")

    all_ok = True
    for pb in playbooks:
        logger.node_header(pb.name)
        rc = _run_playbook(pb, inventory=cfg.inventory,
                           node_filter=node_filter, dry_run=dry_run)
        if rc == 0:
            logger.ok("done")
        else:
            logger.fail(f"failed (exit {rc})")
            all_ok = False
        print()

    return all_ok
