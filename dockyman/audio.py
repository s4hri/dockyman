"""Audio device detection and configuration on each node.

Replaces ``scripts/setup_audio.sh``.  Supports PulseAudio with ALSA fallback.
"""

from __future__ import annotations

from typing import Optional

from .config import Node, Project
from .runner import run_on_node
from . import logger


# ── Listing ──────────────────────────────────────────────────────────────────


def _list_node_audio(node: Node, *, dry_run: bool = False) -> bool:
    logger.node_header(node.node_id)

    # Playback (ALSA)
    logger.info("Playback devices (ALSA):")
    run_on_node(node, "aplay -l 2>&1", dry_run=dry_run)

    # Recording (ALSA)
    logger.info("Recording devices (ALSA):")
    run_on_node(node, "arecord -l 2>&1", dry_run=dry_run)

    # PulseAudio sinks
    logger.info("PulseAudio sinks (output):")
    run_on_node(node, "pactl list short sinks 2>&1", dry_run=dry_run)

    # PulseAudio sources
    logger.info("PulseAudio sources (input):")
    run_on_node(node, "pactl list short sources 2>&1", dry_run=dry_run)

    print()
    return True


def list_audio(project: Project, *, dry_run: bool = False) -> bool:
    """List audio devices on all nodes."""
    logger.header(f"Audio devices for project '{project.name}'")
    all_ok = True
    for node in project.swarm:
        if not _list_node_audio(node, dry_run=dry_run):
            all_ok = False
    return all_ok


# ── Volume ───────────────────────────────────────────────────────────────────


def _set_volume_node(
    node: Node, volume: int, card: Optional[str], *, dry_run: bool = False,
) -> bool:
    """Set output volume on a single node. PulseAudio first, ALSA fallback."""
    logger.node_header(node.node_id)

    if card:
        sink = card
    elif node.audio_card:
        sink = node.audio_card
    else:
        res = run_on_node(
            node,
            "pactl info 2>/dev/null | grep 'Default Sink' | cut -d: -f2 | xargs",
            capture=True, dry_run=dry_run,
        )
        sink = res.stdout if res.ok and res.stdout else None

    if sink:
        logger.info(f"Setting PulseAudio volume to {volume}% on sink: {sink}")
        run_on_node(node, f"pactl set-sink-mute '{sink}' 0", dry_run=dry_run)
        res = run_on_node(node, f"pactl set-sink-volume '{sink}' {volume}%", dry_run=dry_run)
        if res.ok:
            logger.ok(f"Volume set to {volume}%")
            logger.section("Audio Configuration Applied")
            run_on_node(node, f"pactl list sinks | grep -A 15 '{sink}'", capture=True, dry_run=dry_run)
            print()
            return True
        logger.fail("Failed to set PulseAudio volume")

    # ALSA fallback
    alsa_card = card or "0"
    logger.info(f"Setting ALSA volume to {volume}% on card {alsa_card}")
    res = run_on_node(node, f"amixer -c {alsa_card} sset Master {volume}% unmute", dry_run=dry_run)
    if res.ok:
        logger.ok(f"Volume set to {volume}%")
        print()
        return True

    logger.fail("No audio control utility found (pactl or amixer required)")
    print()
    return False


def set_volume(
    project: Project, volume: int, card: Optional[str] = None,
    *, node_id: Optional[str] = None, dry_run: bool = False,
) -> bool:
    """Set audio output volume on matching nodes."""
    logger.header(f"Setting output volume for project '{project.name}'")
    nodes = _filter_nodes(project, node_id)
    return all(_set_volume_node(n, volume, card, dry_run=dry_run) for n in nodes)


# ── Input volume ─────────────────────────────────────────────────────────────


def _set_input_volume_node(
    node: Node, volume: int, source: Optional[str], *, dry_run: bool = False,
) -> bool:
    logger.node_header(node.node_id)

    if source:
        src = source
    elif node.audio_input_card:
        src = node.audio_input_card
    else:
        res = run_on_node(
            node,
            "pactl info 2>/dev/null | grep 'Default Source' | cut -d: -f2 | xargs",
            capture=True, dry_run=dry_run,
        )
        src = res.stdout if res.ok and res.stdout else None

    if src:
        logger.info(f"Setting PulseAudio input volume to {volume}% on source: {src}")
        run_on_node(node, f"pactl set-source-mute '{src}' 0", dry_run=dry_run)
        res = run_on_node(node, f"pactl set-source-volume '{src}' {volume}%", dry_run=dry_run)
        if res.ok:
            logger.ok(f"Input volume set to {volume}%")
            print()
            return True
        logger.fail("Failed to set PulseAudio input volume")

    # ALSA fallback
    alsa_card = source or "0"
    logger.info(f"Setting ALSA input volume to {volume}% on card {alsa_card}")
    res = run_on_node(node, f"amixer -c {alsa_card} sset Capture {volume}% unmute", dry_run=dry_run)
    if res.ok:
        logger.ok(f"Input volume set to {volume}%")
        print()
        return True

    logger.fail("No audio control utility found")
    print()
    return False


def set_input_volume(
    project: Project, volume: int, source: Optional[str] = None,
    *, node_id: Optional[str] = None, dry_run: bool = False,
) -> bool:
    """Set audio input (microphone) volume on matching nodes."""
    logger.header(f"Setting input volume for project '{project.name}'")
    nodes = _filter_nodes(project, node_id)
    return all(_set_input_volume_node(n, volume, source, dry_run=dry_run) for n in nodes)


# ── Mute / unmute ────────────────────────────────────────────────────────────


def _mute_node(
    node: Node, action: str, *, is_input: bool = False, device: Optional[str] = None,
    dry_run: bool = False,
) -> bool:
    logger.node_header(node.node_id)
    mute_val = "1" if action == "mute" else "0"
    kind = "source" if is_input else "sink"

    if not device:
        grep_key = "Default Source" if is_input else "Default Sink"
        res = run_on_node(
            node,
            f"pactl info 2>/dev/null | grep '{grep_key}' | cut -d: -f2 | xargs",
            capture=True, dry_run=dry_run,
        )
        device = res.stdout if res.ok and res.stdout else None

    if device:
        logger.info(f"{action.capitalize()}ing {kind}: {device}")
        res = run_on_node(node, f"pactl set-{kind}-mute '{device}' {mute_val}", dry_run=dry_run)
        if res.ok:
            logger.ok(f"{kind} {action}d")
            print()
            return True

    # ALSA fallback
    alsa_card = device or "0"
    control = "Capture" if is_input else "Master"
    logger.info(f"{action.capitalize()}ing ALSA {control} on card {alsa_card}")
    res = run_on_node(node, f"amixer -c {alsa_card} sset {control} {action}", dry_run=dry_run)
    if res.ok:
        logger.ok(f"{control} {action}d")
        print()
        return True

    logger.fail("No audio control utility found")
    print()
    return False


def mute(
    project: Project, action: str = "mute", *,
    is_input: bool = False, device: Optional[str] = None,
    node_id: Optional[str] = None, dry_run: bool = False,
) -> bool:
    """Mute or unmute audio on matching nodes."""
    kind = "input" if is_input else "output"
    logger.header(f"{action.capitalize()} audio {kind} for project '{project.name}'")
    nodes = _filter_nodes(project, node_id)
    return all(
        _mute_node(n, action, is_input=is_input, device=device, dry_run=dry_run)
        for n in nodes
    )


# ── Audio test ───────────────────────────────────────────────────────────────


def test_audio(
    project: Project, card: Optional[str] = None,
    *, node_id: Optional[str] = None, dry_run: bool = False,
) -> bool:
    """Run a short speaker test on matching nodes."""
    logger.header(f"Audio test for project '{project.name}'")
    nodes = _filter_nodes(project, node_id)
    all_ok = True
    for node in nodes:
        logger.node_header(node.node_id)
        dev = f"-D hw:{card},0 " if card else ""
        logger.info("Running speaker test (2 seconds)…")
        res = run_on_node(node, f"timeout 2 speaker-test -c 2 -t sine -f 1000 {dev}2>/dev/null", dry_run=dry_run)
        if res.ok:
            logger.ok("Audio test completed")
        else:
            logger.fail("speaker-test not found or failed")
            all_ok = False
        print()
    return all_ok


# ── Helpers ──────────────────────────────────────────────────────────────────


def _filter_nodes(project: Project, node_id: Optional[str]) -> list[Node]:
    if node_id:
        return [n for n in project.swarm if n.node_id == node_id]
    return project.swarm
