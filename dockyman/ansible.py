"""Run Ansible playbooks defined in dockyman.yaml."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Optional

from .config import AnsibleConfig, AnsiblePlaybook, Project
from . import logger


def _run_playbook(playbook: AnsiblePlaybook, inventory: str,
                  node_filter: Optional[str] = None,
                  dry_run: bool = False) -> int:
    """Execute a single ansible-playbook command.

    Returns the process exit code (0 = success).
    """
    # Project-scoped playbooks define their own hosts: inside the playbook;
    # no --limit is added so Ansible targets exactly what the playbook declares.
    effective_filter = None if playbook.project_scope else node_filter
    if effective_filter:
        limit = effective_filter
    elif playbook.nodes and playbook.nodes != ["all"]:
        limit = ",".join(playbook.nodes)
    else:
        limit = None

    cmd_parts = ["ansible-playbook", "-i", inventory, playbook.file]
    if playbook.extra_vars:
        cmd_parts += ["--extra-vars", json.dumps(playbook.extra_vars)]

    cmd_str = " ".join(cmd_parts)

    if dry_run:
        print(f"  {logger.YELLOW}[dry-run]{logger.RESET} {cmd_str}")
        return 0

    print(f"  {logger.BOLD}${logger.RESET} {cmd_str}")
    result = subprocess.run(cmd_parts)
    return result.returncode


def _collect_playbooks(project: Project,
                       node_filter: Optional[str] = None) -> list[AnsiblePlaybook]:
    """Collect all playbooks: node-level first, then top-level ansible: section.

    ``node_filter`` limits node-level playbooks to those belonging to the
    named node; top-level playbooks are still included when the named node is
    in their ``nodes`` list (or ``nodes`` is ``["all"]``).
    """
    result: list[AnsiblePlaybook] = []

    # 1. Node-level playbooks (preferred, canonical form)
    for node in project.nodes:
        if node_filter and node.node_id != node_filter:
            continue
        result.extend(node.playbooks)

    # 2. Project-level playbooks — always included; hosts are defined inside each
    #    playbook, so node_filter does not restrict them.
    result.extend(project.project_playbooks)

    # 3. Top-level ansible: section (backward compatibility)
    if project.ansible:
        for pb in project.ansible.playbooks:
            if node_filter:
                if pb.nodes != ["all"] and node_filter not in pb.nodes:
                    continue
            result.append(pb)

    return result


def run_playbooks(project: Project,
                  playbook_filter: Optional[str] = None,
                  node_filter: Optional[str] = None,
                  hook: Optional[str] = None,
                  dry_run: bool = False) -> bool:
    """Run Ansible playbooks declared in the project.

    Playbooks can be defined per-node (under ``nodes.<name>.playbooks:``) or
    in the top-level ``ansible:`` section (backward compatibility).

    Args:
        playbook_filter: When given, only run the playbook with this name.
        node_filter:     When given, only run playbooks belonging to that node.
        hook:            When given, only run playbooks whose ``hook`` matches.
                         When None (explicit ``dockyman ansible`` command), run
                         all playbooks regardless of their hook value.
        dry_run:         Print commands without executing them.

    Returns True if all playbooks succeeded (or there were none to run).
    """
    playbooks = _collect_playbooks(project, node_filter=node_filter)

    if not playbooks and project.ansible is None:
        logger.warn("No playbooks found in project — nothing to run.")
        return True

    # Filter by name if requested
    if playbook_filter:
        playbooks = [p for p in playbooks if p.name == playbook_filter]
        if not playbooks:
            print(f"Error: no playbook named '{playbook_filter}'", file=sys.stderr)
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
        rc = _run_playbook(pb, inventory=project.inventory,
                           node_filter=node_filter, dry_run=dry_run)
        if rc == 0:
            logger.ok("done")
        else:
            logger.fail(f"failed (exit {rc})")
            all_ok = False
        print()

    return all_ok
