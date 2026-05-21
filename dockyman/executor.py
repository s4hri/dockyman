"""Execute docker compose commands across swarm nodes."""

from __future__ import annotations

import os
import subprocess
import signal

from .config import Node, Project
from . import logger


# ── Shell helpers ────────────────────────────────────────────────────────────


def _expand_for_log(cmd: str) -> str:
    """Return *cmd* with shell subexpressions expanded, for display only.

    Invokes ``sh -c 'echo <cmd>'`` directly as a list (no Python
    ``shell=True``) to avoid the extra shell wrapper that would otherwise
    allow metacharacter injection at the Python level.  Falls back to the
    original string on any error or timeout.
    """
    try:
        result = subprocess.run(
            ["sh", "-c", f"echo {cmd}"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return cmd


def _run_shell(cmd: str, cwd: Optional[str] = None, dry_run: bool = False) -> int:
    """Run *cmd* through the shell, streaming output live.

    Returns the process exit code.
    """
    if dry_run:
        if not logger._quiet:
            raw = cmd
            expanded = _expand_for_log(cmd)
            print(f"  {logger.YELLOW}[dry-run]{logger.RESET} {raw}")
            if expanded != raw:
                print(f"  {logger.YELLOW}[dry-run]{logger.RESET} {logger.DIM}→ {expanded}{logger.RESET}")
        return 0

    if not logger._quiet:
        raw = cmd
        expanded = _expand_for_log(cmd)
        print(f"  {logger.BOLD}${logger.RESET} {raw}")
        if expanded != raw:
            print(f"  {logger.BOLD} {logger.RESET} {logger.DIM}→ {expanded}{logger.RESET}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode


def _build_compose_cmd(project: Project, node: Node, action: str, command_type: str = "",
                       include_extra_args: bool = True,
                       profile_override: list[str] | None = None) -> str:
    """Build the full shell command string for a node.

    *command_type* selects the profiles and extra CLI args (``shell_prefix``
    is always prepended for all command types):
    ``"build"``        → ``shell_prefix`` + ``build_profiles`` + ``build_args``,
    ``"run"``          → ``shell_prefix`` + ``run_profiles``   + ``run_args``,
    ``"pull"``         → ``shell_prefix`` + ``pull_profiles`` (or ``run_profiles``),
    ``"push"``         → ``shell_prefix`` + ``push_profiles`` (or ``run_profiles``),
    ``"down"``         → ``shell_prefix`` + ``down_profiles`` (or ``run_profiles``) + ``down_args``,
    ``"config_build"`` → ``shell_prefix`` + ``build_profiles``,
    ``"config_run"``   → ``shell_prefix`` + ``run_profiles``.

    *profile_override*, when provided, replaces the profile list derived from
    *command_type*.  Use this to pass a pre-filtered or pre-merged profile list.

    Set *include_extra_args* to False to include env vars and profiles
    but omit the extra CLI args (e.g. ``--remove-orphans``).
    """
    env_prefix = node.get_env_prefix(command_type)

    # Select profiles and extra compose CLI args
    if command_type == "build":
        profiles = node.build_profiles
        extra_args = node.build_args.strip()
    elif command_type == "run":
        profiles = node.run_profiles
        extra_args = node.run_args.strip()
    elif command_type == "pull":
        # Fall back to run_profiles when no pull-specific profiles are set.
        profiles = node.pull_profiles if node.pull_profiles is not None else node.run_profiles
        extra_args = ""
    elif command_type == "push":
        # Fall back to run_profiles when no push-specific profiles are set.
        profiles = node.push_profiles if node.push_profiles is not None else node.run_profiles
        extra_args = ""
    elif command_type == "down":
        # Fall back to run_profiles when no down-specific profiles are set.
        profiles = node.down_profiles if node.down_profiles is not None else node.run_profiles
        extra_args = node.down_args.strip()
    elif command_type == "config":
        # All profiles defined for the node, deduplicated, preserving order
        seen: set[str] = set()
        profiles = []
        for p in node.build_profiles + node.run_profiles:
            if p not in seen:
                seen.add(p)
                profiles.append(p)
        extra_args = ""
    elif command_type == "config_build":
        profiles = node.build_profiles
        extra_args = ""
    elif command_type == "config_run":
        profiles = node.run_profiles
        extra_args = ""
    else:
        profiles = []
        extra_args = ""

    if profile_override is not None:
        profiles = profile_override

    cmd_parts = []
    if env_prefix:
        cmd_parts.append(env_prefix)

    compose_parts = ["docker compose"]
    for cf in node.compose_files:
        compose_parts.append(f"-f {os.path.join(project.base_dir, node.docker_context, cf)}")
    for ef in node.env_files:
        compose_parts.append(f"--env-file {os.path.join(project.base_dir, node.docker_context, ef)}")
    for profile in profiles:
        compose_parts.append(f"--profile {profile}")
    compose = " ".join(compose_parts)

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

    for node in project.nodes:
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


def pull(project: Project, dry_run: bool = False) -> bool:
    """Run ``docker compose pull`` on every node.

    Uses ``pull_profiles`` when set; falls back to ``run_profiles`` otherwise.
    Returns True if all pulls succeeded.
    """
    logger.header(f"Pulling images for project '{project.name}' …")
    all_ok = True

    for node in project.nodes:
        logger.node_header(node.node_id)
        cmd = _build_compose_cmd(project, node, "pull", command_type="pull")
        rc = _run_shell(cmd, dry_run=dry_run)
        if rc == 0:
            logger.ok("pull succeeded")
        else:
            logger.fail("pull failed")
            all_ok = False
        print()

    return all_ok


def push(project: Project, dry_run: bool = False) -> bool:
    """Run ``docker compose push`` on every node.

    Uses ``push_profiles`` when set. Returns True if all pushes succeeded.
    """
    logger.header(f"Pushing images for project '{project.name}' …")
    all_ok = True

    for node in project.nodes:
        logger.node_header(node.node_id)
        cmd = _build_compose_cmd(project, node, "push", command_type="push")
        rc = _run_shell(cmd, dry_run=dry_run)
        if rc == 0:
            logger.ok("push succeeded")
        else:
            logger.fail("push failed")
            all_ok = False
        print()

    return all_ok


def build(project: Project, dry_run: bool = False) -> bool:
    """Run ``docker compose --profile build build`` on every node.

    Returns True if all builds succeeded.
    """
    logger.header(f"Building services for project '{project.name}' …")
    all_ok = True

    for node in project.nodes:
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
        log_dir: str | None = None) -> bool:
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

    # ── 0. Log config + hardware info ────────────────────────────────────
    from .hardware import detect_hardware as hw_detect
    if project.config_log_dir:
        hw_detect(project, dry_run=dry_run, _show_header=False)
        logger.close_log()

    # ── 1. Start containers (always detached) ────────────────────────────
    for node in project.nodes:
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
    log_paths: list[str] = []

    for node in project.nodes:
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
                log_paths.append(log_path)
                cmd = _build_compose_cmd(project, node, f"logs -f {service}", command_type="run",
                                                include_extra_args=False)

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
    for node in project.nodes:
        logger.info(f"  [{node.node_id}] up")
    if log_dir:
        for p in log_paths:
            logger.info(f"  Log → {p}")
    print()

    if not dry_run:
        try:
            input(f"{logger.BOLD}Press ENTER to stop all containers …{logger.RESET}")
            print()
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

    Uses ``down_profiles`` when set; falls back to ``run_profiles`` otherwise.
    Returns True if all nodes tore down successfully.
    """
    logger.header(f"Stopping services for project '{project.name}' …")
    all_ok = True

    for node in project.nodes:
        logger.node_header(node.node_id)
        cmd = _build_compose_cmd(project, node, "down", command_type="down")
        rc = _run_shell(cmd, dry_run=dry_run)
        if rc == 0:
            logger.ok("down")
        else:
            logger.fail("failed to stop")
            all_ok = False
        print()

    return all_ok


def config(project: Project, dry_run: bool = False,
           node_filter: str | None = None,
           profile_filter: list[str] | None = None,
           stage: str | None = None) -> bool:
    """Run ``docker compose config`` on every node to show resolved config.

    Args:
        node_filter:    When given, only process the node with this ID.
        profile_filter: When given, only activate profiles from this list
                        (intersected with each node's stage-appropriate profiles).
                        When omitted, all relevant profiles for the node are used.
        stage:          ``"build"`` \u2192 ``build_profiles``;
                        ``"run"``   \u2192 ``run_profiles``;
                        ``None``    → merge both (default).

    Returns True if all matched nodes resolved successfully.
    """
    logger.header(f"Resolved compose config for project '{project.name}' …")
    all_ok = True

    nodes = project.nodes
    if node_filter:
        nodes = [n for n in nodes if n.node_id == node_filter]
        if not nodes:
            import sys as _sys
            print(f"Error: no node with id '{node_filter}'", file=_sys.stderr)
            return False

    # Map stage to the command_type understood by _build_compose_cmd
    command_type = f"config_{stage}" if stage else "config"

    for node in nodes:
        logger.node_header(node.node_id)

        # Candidate profiles depend on the stage
        if stage == "build":
            candidate = node.build_profiles
        elif stage == "run":
            candidate = node.run_profiles
        else:
            # All profiles for the node, deduplicated, preserving order
            seen: set[str] = set()
            candidate = []
            for p in node.build_profiles + node.run_profiles:
                if p not in seen:
                    seen.add(p)
                    candidate.append(p)

        # Optionally narrow down by the --profile filter
        if profile_filter is not None:
            allowed = set(profile_filter)
            profiles: list[str] | None = [p for p in candidate if p in allowed]
        else:
            profiles = candidate

        cmd = _build_compose_cmd(project, node, "config",
                                 command_type=command_type,
                                 profile_override=profiles)
        rc = _run_shell(cmd, dry_run=dry_run)
        if rc != 0:
            all_ok = False
        print()

    return all_ok
