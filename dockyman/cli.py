"""dockyman CLI – orchestrate Docker Compose across a swarm."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import load_config
from .executor import build, config, down, run, status
from .hardware import detect_hardware, setup
from . import logger


def _add_node_arg(parser: argparse.ArgumentParser) -> None:
    """Add the common --node filter argument."""
    parser.add_argument(
        "-n", "--node", default=None, metavar="NODE_ID",
        help="Limit to a specific node (default: all nodes).",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="dockyman",
        description="Orchestrate Docker Compose services across multiple machines.",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-f",
        "--file",
        default="dockyman.yaml",
        help="Path to the dockyman.yaml config file (default: dockyman.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    # Removed --log argument; per-node logs only

    sub = parser.add_subparsers(dest="command", required=True)

    # -- status ----------------------------------------------------------------
    sub.add_parser("status", help="Check that all docker hosts are reachable.")

    # -- build -----------------------------------------------------------------
    sub.add_parser("build", help="Build images on all nodes.")

    # -- run -------------------------------------------------------------------
    run_parser = sub.add_parser("run", help="Start services on all nodes.")
    run_parser.add_argument(
        "-d", "--detach", action="store_true",
        help="Run containers in the background and exit immediately.",
    )
    run_parser.add_argument(
        "--log-output", default=None, metavar="DIR",
        help="Save container logs to files in DIR instead of printing to stdout.",
    )

    # -- down ------------------------------------------------------------------
    sub.add_parser("down", help="Stop services on all nodes.")

    # -- config ----------------------------------------------------------------
    sub.add_parser("config", help="Show resolved compose config on all nodes.")

    # -- info ------------------------------------------------------------------
    info_parser = sub.add_parser("info", help="Detect hardware on all nodes.")
    _add_node_arg(info_parser)

    # -- setup -----------------------------------------------------------------
    sub.add_parser("setup", help="Run setup_script on each node (display, audio, environment, etc.).")

    # ── Parse & dispatch ─────────────────────────────────────────────────────
    args = parser.parse_args(argv)

    # No global log; per-node logs only

    # Load project configuration
    try:
        project = load_config(args.file)
    except (FileNotFoundError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    dry = args.dry_run
    ok = True

    match args.command:
        # compose commands
        case "status":
            ok = status(project, dry_run=dry)
        case "build":
            ok = build(project, dry_run=dry)
        case "run":
            log_dir = args.log_output if args.log_output else (project.log_dir or None)
            ok = run(project, dry_run=dry, detach=args.detach,
                     log_dir=log_dir)
        case "down":
            ok = down(project, dry_run=dry)
        case "config":
            ok = config(project, dry_run=dry)

        # hardware info
        case "info":
            ok = detect_hardware(project, dry_run=dry)

        # hardware setup
        case "setup":
            ok = setup(project, dry_run=dry)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
