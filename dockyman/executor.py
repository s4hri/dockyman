"""Execute docker compose commands across swarm nodes."""

from __future__ import annotations

import os
import subprocess
import signal
from typing import Optional

from .config import Node, Project
from . import logger


# ── Shell helpers ────────────────────────────────────────────────────────────


def _run_shell(cmd: str, cwd: Optional[str] = None, dry_run: bool = False) -> int:
    """Run *cmd* through the shell, streaming output live.

    Returns the process exit code.
    """
    if dry_run:
        if not logger._quiet:
            print(f"  {logger.YELLOW}[dry-run]{logger.RESET} {cmd}")
        return 0

    if not logger._quiet:
        print(f"  {logger.BOLD}${logger.RESET} {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode


def _build_compose_cmd(project: Project, node: Node, action: str, command_type: str = "",
                       include_extra_args: bool = True) -> str:
    """Build the full shell command string for a node.

    *command_type* selects env vars, profiles, and extra CLI args:
    ``"build"`` → ``build_env_vars`` + ``build_profiles`` + ``build_args``,
    ``"run"``   → ``run_env_vars``   + ``run_profiles``   + ``run_args``.

    Set *include_extra_args* to False to include env vars and profiles
    but omit the extra CLI args (e.g. ``--remove-orphans``).
    """
    compose_file = os.path.join(project.base_dir, node.docker_context, node.compose_file)
    env_prefix = node.get_env_prefix(command_type)

    # Select profiles and extra compose CLI args
    if command_type == "build":
        profiles = node.build_profiles
        extra_args = node.build_args.strip()
    elif command_type == "run":
        profiles = node.run_profiles
        extra_args = node.run_args.strip()
    else:
        profiles = []
        extra_args = ""

    cmd_parts = []
    if env_prefix:
        cmd_parts.append(env_prefix)

    compose = f"docker compose -f {compose_file}"
    if node.env_file:
        env_file_path = os.path.join(project.base_dir, node.docker_context, node.env_file)
        compose += f" --env-file {env_file_path}"
    for profile in profiles:
        compose += f" --profile {profile}"

    cmd_parts.append(compose)
    cmd_parts.append(action)
    if include_extra_args and extra_args:
        cmd_parts.append(extra_args)

    return " ".join(cmd_parts)


# ── Public commands ──────────────────────────────────────────────────────────


def status(project: Project, dry_run: bool = False) -> bool:
    """Check connectivity to every Docker host in the swarm.

    Runs ``docker info`` against each node's DOCKER_HOST.
    Returns True if all nodes are reachable.
    """
    logger.header(f"Checking swarm status for project '{project.name}' …")
    all_ok = True

    for node in project.swarm:
        logger.node_header(node.node_id)
        env_prefix = node.get_env_prefix("run")
        cmd = (
            f"{env_prefix} docker info --format '{{{{.Name}}}}'" if env_prefix
            else "docker info --format '{{.Name}}'"
        )
        rc = _run_shell(cmd, dry_run=dry_run)
        if rc == 0:
            logger.ok("reachable")
        else:
            logger.fail("unreachable")
            all_ok = False
        print()

    return all_ok


def build(project: Project, dry_run: bool = False) -> bool:
    """Run ``docker compose --profile build build`` on every node.

    Returns True if all builds succeeded.
    """
    logger.header(f"Building services for project '{project.name}' …")
    all_ok = True

    for node in project.swarm:
        logger.node_header(node.node_id)
        cmd = _build_compose_cmd(project, node, "build", command_type="build")
        rc = _run_shell(cmd, dry_run=dry_run)
        if rc == 0:
            logger.ok("build succeeded")
        else:
            logger.fail("build failed")
            all_ok = False
        print()

    return all_ok


def run(project: Project, dry_run: bool = False, detach: bool = False,
        log_dir: Optional[str] = None) -> bool:
    """Start services on every node.

    Default behaviour (no flags):
      1. Start all containers detached (``up -d``).
      2. Stream container logs to stdout (or to files if *log_dir* is set).
      3. Print a summary and wait for the user to press ENTER.
      4. Tear down all containers (``down``).

    With ``--detach``: start detached and return immediately.
    With ``--log-output DIR``: save logs to ``DIR/<node_id>.log`` files.
    """
    logger.header(f"Running services for project '{project.name}' …")
    all_ok = True

    # ── 0. Apply hardware setup + detect info (quiet – logs only) ────────
    from .hardware import setup as hw_setup, detect_hardware
    logger.info("Applying hardware settings and detecting node info …")
    with logger.quiet_mode():
        hw_setup(project, dry_run=dry_run)
        detect_hardware(project, dry_run=dry_run)

    # ── 1. Start containers (always detached) ────────────────────────────
    for node in project.swarm:
        logger.node_header(node.node_id)
        cmd = _build_compose_cmd(project, node, "up -d", command_type="run")
        rc = _run_shell(cmd, dry_run=dry_run)
        if rc == 0:
            logger.ok("started")
        else:
            logger.fail("failed to start")
            all_ok = False
        print()

    if not all_ok:
        return False

    # If --detach, exit immediately
    if detach:
        logger.info("Containers running in background (detached).")
        return True

    # ── 2. Stream / save container logs ──────────────────────────────────
    log_processes: list[subprocess.Popen] = []
    log_files: list = []

    for node in project.swarm:
        if log_dir:
            # Get the list of services for this node
            svc_cmd = _build_compose_cmd(project, node, "config --services", command_type="run",
                                                include_extra_args=False)
            if dry_run:
                node_log_dir = os.path.join(log_dir, node.node_id)
                print(f"  {logger.YELLOW}[dry-run]{logger.RESET} {svc_cmd}")
                print(f"  {logger.YELLOW}[dry-run]{logger.RESET} "
                      f"For each service: logs -f <service> > {node_log_dir}/<service>.log")
                continue

            result = subprocess.run(svc_cmd, shell=True, capture_output=True, text=True)
            services = [s.strip() for s in result.stdout.strip().splitlines() if s.strip()]

            if not services:
                logger.warn(f"[{node.node_id}] No services found, skipping logs")
                continue

            node_log_dir = os.path.join(log_dir, node.node_id)
            os.makedirs(node_log_dir, exist_ok=True)

            for service in services:
                log_path = os.path.join(node_log_dir, f"{service}.log")
                fh = open(log_path, "w")
                log_files.append(fh)
                cmd = _build_compose_cmd(project, node, f"logs -f {service}", command_type="run",
                                                include_extra_args=False)
                logger.info(f"[{node.node_id}] {service} → {log_path}")
                proc = subprocess.Popen(cmd, shell=True, stdout=fh, stderr=subprocess.STDOUT)
                log_processes.append(proc)
        else:
            cmd = _build_compose_cmd(project, node, "logs -f", command_type="run",
                                            include_extra_args=False)
            if dry_run:
                print(f"  {logger.YELLOW}[dry-run]{logger.RESET} {cmd}")
                continue
            proc = subprocess.Popen(cmd, shell=True)
            log_processes.append(proc)

    # ── 3. Summary + wait for ENTER ──────────────────────────────────────
    print()
    logger.header("All services are running.")
    for node in project.swarm:
        logger.info(f"  [{node.node_id}] up")
    if log_dir:
        logger.info(f"  Logs → {os.path.abspath(log_dir)}/<node_id>/<service>.log")
    print()

    if not dry_run:
        try:
            input(f"{logger.BOLD}Press ENTER to stop all containers …{logger.RESET}")
        except (KeyboardInterrupt, EOFError):
            print()

    # ── 4. Stop log streaming ────────────────────────────────────────────
    for proc in log_processes:
        proc.send_signal(signal.SIGTERM)
        proc.wait()
    for fh in log_files:
        fh.close()

    # ── 5. Tear down containers ──────────────────────────────────────────
    print()
    return down(project, dry_run=dry_run)


def down(project: Project, dry_run: bool = False) -> bool:
    """Run ``docker compose down`` on every node.

    Returns True if all nodes tore down successfully.
    """
    logger.header(f"Stopping services for project '{project.name}' …")
    all_ok = True

    for node in project.swarm:
        logger.node_header(node.node_id)
        cmd = _build_compose_cmd(project, node, "down", command_type="run")
        rc = _run_shell(cmd, dry_run=dry_run)
        if rc == 0:
            logger.ok("down")
        else:
            logger.fail("failed to stop")
            all_ok = False
        print()

    return all_ok


def config(project: Project, dry_run: bool = False) -> bool:
    """Run ``docker compose config`` on every node to show resolved config.

    Returns True if all nodes resolved successfully.
    """
    logger.header(f"Resolved compose config for project '{project.name}' …")
    all_ok = True

    for node in project.swarm:
        logger.node_header(node.node_id)
        cmd = _build_compose_cmd(project, node, "config", command_type="run")
        rc = _run_shell(cmd, dry_run=dry_run)
        if rc != 0:
            all_ok = False
        print()

    return all_ok
