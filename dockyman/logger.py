"""Structured logging to console and a run‑log file."""

from __future__ import annotations

import datetime
import os
import platform
import socket
from pathlib import Path

# ── Colours (console only) ───────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
CYAN = "\033[36m"
YELLOW = "\033[33m"

_log_path: str | None = None
_quiet: bool = False


class quiet_mode:
    """Context manager that suppresses console output while still writing to the log file."""

    def __enter__(self):
        global _quiet
        _quiet = True
        return self

    def __exit__(self, *exc):
        global _quiet
        _quiet = False
        return False


def init_log(path: str = "lastrun.log") -> None:
    """Create / reset the log file with a header."""
    global _log_path
    _log_path = os.path.abspath(path)
    with open(_log_path, "w") as fh:
        fh.write(f"=== Dockyman Node Hardware Log ===\n")
        fh.write(f"Date: {datetime.datetime.now()}\n")
        fh.write(f"User: {os.environ.get('USER', 'unknown')}\n")
        fh.write(f"Hostname: {socket.gethostname()}\n")
        fh.write("================================\n\n")


def _write(msg: str) -> None:
    if _log_path:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(_log_path, "a") as fh:
            fh.write(f"{ts} {msg}\n")


def info(msg: str) -> None:
    tag = f"[INFO] {msg}"
    if not _quiet:
        print(f"{GREEN}{tag}{RESET}")
    _write(tag)


def warn(msg: str) -> None:
    tag = f"[WARNING] {msg}"
    if not _quiet:
        print(f"{YELLOW}{tag}{RESET}")
    _write(tag)


def error(msg: str) -> None:
    tag = f"[ERROR] {msg}"
    if not _quiet:
        print(f"{RED}{tag}{RESET}")
    _write(tag)


def section(title: str) -> None:
    """Write a section header to the log file."""
    _write(f"\n--- {title} ---")


def log_raw(text: str) -> None:
    """Append raw text to the log file only (no console)."""
    if _log_path:
        with open(_log_path, "a") as fh:
            fh.write(text + "\n")


def saved(path: str) -> None:
    """Print the path of a written log file, always (bypasses quiet mode)."""
    print(f"{CYAN}  → config log: {path}{RESET}")
    _write(f"  -> config log: {path}")


def header(text: str) -> None:
    """Print a bold header to the console and log."""
    if not _quiet:
        print(f"\n{BOLD}{text}{RESET}\n")
    _write(f"\n{'=' * 40}")
    _write(text)
    _write("=" * 40)


def node_header(node_id: str) -> None:
    if not _quiet:
        print(f"{BOLD}{CYAN}[{node_id}]{RESET}")
    _write(f"[{node_id}]")

def ok(msg: str) -> None:
    if not _quiet:
        print(f"  {GREEN}✔ {msg}{RESET}")
    _write(f"  ✔ {msg}")


def fail(msg: str) -> None:
    if not _quiet:
        print(f"  {RED}✘ {msg}{RESET}")
    _write(f"  ✘ {msg}")
