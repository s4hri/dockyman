"""dockyman CLI – orchestrate Docker Compose across a swarm."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import load_config
from .executor import build, config, down, run, status
from .hardware import detect_hardware, setup
from .audio import list_audio, set_volume, set_input_volume, mute, test_audio
from .display import list_displays, apply_display
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
    sub.add_parser("setup", help="Apply display and audio settings from dockyman.yaml.")

    # -- audio -----------------------------------------------------------------
    audio_parser = sub.add_parser("audio", help="Audio device management.")
    audio_sub = audio_parser.add_subparsers(dest="audio_command", required=True)

    #   audio list
    audio_list = audio_sub.add_parser("list", help="List audio devices.")
    _add_node_arg(audio_list)

    #   audio volume <level>
    audio_vol = audio_sub.add_parser("volume", help="Set output volume (0-100).")
    audio_vol.add_argument("level", type=int, help="Volume level 0-100.")
    audio_vol.add_argument("--card", default=None, help="Sink / card identifier.")
    _add_node_arg(audio_vol)

    #   audio input-volume <level>
    audio_ivol = audio_sub.add_parser("input-volume", help="Set input (mic) volume (0-100).")
    audio_ivol.add_argument("level", type=int, help="Volume level 0-100.")
    audio_ivol.add_argument("--source", default=None, help="Source identifier.")
    _add_node_arg(audio_ivol)

    #   audio mute / unmute
    audio_mute = audio_sub.add_parser("mute", help="Mute audio output.")
    audio_mute.add_argument("--input", action="store_true", help="Mute input instead.")
    audio_mute.add_argument("--device", default=None, help="Sink/source identifier.")
    _add_node_arg(audio_mute)

    audio_unmute = audio_sub.add_parser("unmute", help="Unmute audio output.")
    audio_unmute.add_argument("--input", action="store_true", help="Unmute input instead.")
    audio_unmute.add_argument("--device", default=None, help="Sink/source identifier.")
    _add_node_arg(audio_unmute)

    #   audio test
    audio_test = audio_sub.add_parser("test", help="Run a short speaker test.")
    audio_test.add_argument("--card", default=None, help="ALSA card identifier.")
    _add_node_arg(audio_test)

    # -- display ---------------------------------------------------------------
    disp_parser = sub.add_parser("display", help="Display / xrandr management.")
    disp_sub = disp_parser.add_subparsers(dest="display_command", required=True)

    #   display list
    disp_list = disp_sub.add_parser("list", help="List connected displays.")
    _add_node_arg(disp_list)

    #   display apply [XRANDR_ARGS]
    disp_apply = disp_sub.add_parser("apply", help="Apply xrandr configuration (auto-detect if omitted).")
    disp_apply.add_argument("xrandr_args", nargs="?", default=None, help="Custom xrandr arguments.")
    _add_node_arg(disp_apply)

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

        # hardware setup (display + audio from yaml)
        case "setup":
            ok = setup(project, dry_run=dry)

        # audio
        case "audio":
            match args.audio_command:
                case "list":
                    ok = list_audio(project, dry_run=dry)
                case "volume":
                    ok = set_volume(project, args.level, args.card, node_id=getattr(args, "node", None), dry_run=dry)
                case "input-volume":
                    ok = set_input_volume(project, args.level, args.source, node_id=getattr(args, "node", None), dry_run=dry)
                case "mute":
                    ok = mute(project, "mute", is_input=args.input, device=args.device, node_id=getattr(args, "node", None), dry_run=dry)
                case "unmute":
                    ok = mute(project, "unmute", is_input=args.input, device=args.device, node_id=getattr(args, "node", None), dry_run=dry)
                case "test":
                    ok = test_audio(project, args.card, node_id=getattr(args, "node", None), dry_run=dry)

        # display
        case "display":
            match args.display_command:
                case "list":
                    ok = list_displays(project, node_id=getattr(args, "node", None), dry_run=dry)
                case "apply":
                    ok = apply_display(project, args.xrandr_args, node_id=getattr(args, "node", None), dry_run=dry)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
