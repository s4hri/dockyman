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
    compose_files: List[str]
    docker_context: str = ""
    docker_host: Optional[str] = None
    env_files: List[str] = field(default_factory=list)
    build_shell_prefix: str = ""
    build_profiles: List[str] = field(default_factory=list)
    build_args: str = ""
    run_shell_prefix: str = ""
    run_profiles: List[str] = field(default_factory=list)
    run_args: str = ""

    # Shell commands executed on this node during ``dockyman setup`` / ``dockyman run``.
    # Runs locally or via SSH for remote nodes.  Use this for xrandr, pactl, etc.
    setup_script: str = ""

    def get_env_prefix(self, command_type: str = "") -> str:
        """Return the env‑var prefix for the given command type.

        Always includes ``DOCKER_HOST`` when set.  Then appends
        ``build_shell_prefix`` or ``run_shell_prefix`` depending on *command_type*.
        """
        parts: list[str] = []
        if self.docker_host:
            parts.append(f"DOCKER_HOST={self.docker_host}")
        if command_type == "build" and self.build_shell_prefix.strip():
            parts.append(self.build_shell_prefix.strip())
        elif command_type == "run" and self.run_shell_prefix.strip():
            parts.append(self.run_shell_prefix.strip())
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


def _to_list(value) -> List[str]:
    """Coerce a YAML value (string or list) to a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


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
                compose_files=_to_list(node_raw.get("compose_files") or node_raw.get("compose_file")),
                docker_context=node_raw.get("docker_context", ""),
                docker_host=node_raw.get("docker_host"),
                env_files=_to_list(node_raw.get("env_files") or node_raw.get("env_file")),
                build_shell_prefix=node_raw.get("build_shell_prefix", ""),
                build_profiles=node_raw.get("build_profiles", []),
                build_args=node_raw.get("build_args", ""),
                run_shell_prefix=node_raw.get("run_shell_prefix", ""),
                run_profiles=node_raw.get("run_profiles", []),
                run_args=node_raw.get("run_args", ""),
                setup_script=node_raw.get("setup_script", ""),
            )
        )

    project = Project(
        name=proj_raw["name"],
        dockyman_version=str(proj_raw["dockyman_version"]),
        swarm=nodes,
        log_dir=proj_raw.get("log_dir", ""),
    )
    project.base_dir = str(Path(base_dir).resolve())
    # Resolve log_dir relative to the config file location
    if project.log_dir:
        project.log_dir = str((Path(project.base_dir) / project.log_dir).resolve())

    return project
