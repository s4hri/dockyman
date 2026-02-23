"""Parse and validate dockyman.yaml configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class Node:
    """A single node in the swarm."""

    node_id: str
    compose_file: str
    docker_context: str = ""
    docker_host: Optional[str] = None
    env_file: str = ""
    build_env_vars: str = ""
    build_profiles: List[str] = field(default_factory=list)
    build_args: str = ""
    run_env_vars: str = ""
    run_profiles: List[str] = field(default_factory=list)
    run_args: str = ""

    # Hardware configuration (applied by ``dockyman setup``)
    display: str = ""              # X11 DISPLAY value (e.g. ":0", needed for remote)
    display_args: str = ""         # xrandr arguments (auto-detect if empty)
    audio_volume: Optional[int] = None       # output volume 0-100
    audio_card: str = ""           # PulseAudio sink (default if empty)
    audio_input_volume: Optional[int] = None # input volume 0-100
    audio_input_card: str = ""     # PulseAudio source (default if empty)

    def get_env_prefix(self, command_type: str = "") -> str:
        """Return the env‑var prefix for the given command type.

        Always includes ``DOCKER_HOST`` when set.  Then appends
        ``build_env_vars`` or ``run_env_vars`` depending on *command_type*.
        """
        parts: list[str] = []
        if self.docker_host:
            parts.append(f"DOCKER_HOST={self.docker_host}")
        if command_type == "build" and self.build_env_vars.strip():
            parts.append(self.build_env_vars.strip())
        elif command_type == "run" and self.run_env_vars.strip():
            parts.append(self.run_env_vars.strip())
        return " ".join(parts)

    @property
    def is_remote(self) -> bool:
        """True when the node targets a remote Docker daemon (ssh://)."""
        return self.docker_host is not None and self.docker_host.startswith("ssh://")


@dataclass
class Project:
    """Top‑level project configuration."""

    name: str
    dockyman_version: str
    swarm: List[Node]
    log_dir: str = ""

    # Set after loading – absolute path to the dockyman.yaml directory.
    base_dir: str = ""


def load_config(config_path: str = "dockyman.yaml") -> Project:
    """Load *dockyman.yaml* and return a :class:`Project`."""
    config_path = os.path.abspath(config_path)
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as fh:
        raw = yaml.safe_load(fh)

    proj_raw = raw["project"]
    base_dir = os.path.dirname(config_path)

    nodes: list[Node] = []
    for node_raw in proj_raw.get("swarm", []):
        nodes.append(
            Node(
                node_id=node_raw["node_id"],
                compose_file=node_raw["compose_file"],
                docker_context=node_raw.get("docker_context", ""),
                docker_host=node_raw.get("docker_host"),
                env_file=node_raw.get("env_file", ""),
                build_env_vars=node_raw.get("build_env_vars", ""),
                build_profiles=node_raw.get("build_profiles", []),
                build_args=node_raw.get("build_args", ""),
                run_env_vars=node_raw.get("run_env_vars", ""),
                run_profiles=node_raw.get("run_profiles", []),
                run_args=node_raw.get("run_args", ""),
                display=node_raw.get("display", ""),
                display_args=node_raw.get("display_args", ""),
                audio_volume=node_raw.get("audio_volume"),
                audio_card=node_raw.get("audio_card", ""),
                audio_input_volume=node_raw.get("audio_input_volume"),
                audio_input_card=node_raw.get("audio_input_card", ""),
            )
        )

    project = Project(
        name=proj_raw["name"],
        dockyman_version=str(proj_raw["dockyman_version"]),
        swarm=nodes,
        log_dir=proj_raw.get("log_dir", ""),
    )
    project.base_dir = str(Path(base_dir).resolve())

    return project
