"""Parse and validate dockyman.yaml configuration."""

from __future__ import annotations

import getpass
import os
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, UndefinedError


@dataclass
class AnsiblePlaybook:
    """A single Ansible playbook entry."""

    name: str                       # logical name used with --playbook filter
    file: str                       # path to the .yml playbook, relative to dockyman.yaml
    nodes: List[str]                # ["all"] or explicit list of node_ids
    hook: str = ""                  # lifecycle hook: before_build | before_run | after_run | after_down


@dataclass
class AnsibleConfig:
    """Top-level ansible: section from dockyman.yaml."""

    inventory: str                  # path to the Ansible inventory file
    playbooks: List[AnsiblePlaybook] = field(default_factory=list)


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
            
        if command_type in ["build", "config_build"] and self.build_shell_prefix.strip():
            parts.append(self.build_shell_prefix.strip())
        elif command_type in ["run", "config_run"] and self.run_shell_prefix.strip():
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
    dockyman_repo: str
    dockyman_ref: str
    swarm: List[Node]
    container_log_dir: str = ""
    config_log_dir: str = ""
    ansible: Optional[AnsibleConfig] = None

    # Set after loading – absolute path to the dockyman.yaml directory.
    base_dir: str = ""


def _to_list(value) -> List[str]:
    """Coerce a YAML value (string or list) to a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _load_ansible_inventory(config_dir: Path) -> dict[str, SimpleNamespace]:
    """Return {hostname: SimpleNamespace} from the Ansible inventory if present.

    Reads two sources and merges them (later sources win):
      1. inventory/hosts.yaml  — per-host ansible_host / ansible_user / etc.
      2. inventory/vars.yaml   — 'all:' block for shared defaults, then per-host
                                 blocks keyed by hostname.

    String values are resolved as Jinja2 templates iteratively so vars can
    reference each other (e.g. docker_host can embed ansible_host).

    Falls back to an empty dict when no inventory/ directory exists.
    """
    inv_dir = config_dir / "inventory"
    if not inv_dir.is_dir():
        return {}

    # 1. Per-host ansible vars from hosts.yaml (ansible_host, ansible_connection, …)
    hosts_ansible_vars: dict[str, dict] = {}
    hosts_file = inv_dir / "hosts.yaml"
    if hosts_file.exists():
        hosts_data = yaml.safe_load(hosts_file.read_text()) or {}
        for group in hosts_data.values():
            for hostname, hvars in (group.get("hosts") or {}).items():
                hosts_ansible_vars[hostname] = hvars or {}

    # 2. vars.yaml: 'all' key = shared defaults, other keys = per-host overrides
    group_all: dict = {}
    host_vars: dict[str, dict] = {}
    vars_file = inv_dir / "vars.yaml"
    if vars_file.exists():
        vars_data = yaml.safe_load(vars_file.read_text()) or {}
        group_all = vars_data.pop("all", {}) or {}
        host_vars = {k: v or {} for k, v in vars_data.items()}

    # 3. Collect all known hosts
    all_hosts = set(hosts_ansible_vars.keys()) | set(host_vars.keys())
    if not all_hosts:
        return {}

    _jinja_strict = Environment(undefined=StrictUndefined)
    current_user = getpass.getuser()

    def _resolve_pass1(vals: dict, context: dict) -> dict:
        """Resolve intra-host refs; preserve strings that reference unknown vars
        (cross-host refs like {{ worker.ansible_host }}) for pass 2."""
        resolved = dict(vals)
        for _ in range(10):
            new = {}
            changed = False
            for k, v in resolved.items():
                if not isinstance(v, str):
                    new[k] = v
                    continue
                try:
                    rendered = _jinja_strict.from_string(v).render(**context)
                    new[k] = rendered
                    if rendered != v:
                        changed = True
                except UndefinedError:
                    new[k] = v  # keep original template for pass 2
            resolved = new
            context = {**context, **resolved}
            if not changed:
                break
        return resolved

    def _resolve_pass2(vals: dict, context: dict) -> dict:
        """Final render with all peer namespaces available; strict."""
        resolved = dict(vals)
        for _ in range(10):
            new = {
                k: _jinja_strict.from_string(v).render(**context) if isinstance(v, str) else v
                for k, v in resolved.items()
            }
            if new == resolved:
                break
            resolved = new
            context = {**context, **resolved}
        return resolved

    # Pass 1: resolve intra-host references only; cross-host refs are
    # preserved as template strings for pass 2.
    pass1: dict[str, dict] = {}
    for hostname in sorted(all_hosts):
        merged = {
            "current_user": current_user,
            **group_all,
            **hosts_ansible_vars.get(hostname, {}),
            **host_vars.get(hostname, {}),
        }
        merged.setdefault("ansible_user", current_user)
        pass1[hostname] = _resolve_pass1(merged, dict(merged))

    # Pass 2: re-render with all peer namespaces injected so cross-host
    # references like {{ worker.ansible_host }} resolve correctly.
    peers = {h: SimpleNamespace(**v) for h, v in pass1.items()}
    result: dict[str, SimpleNamespace] = {}
    for hostname, resolved in pass1.items():
        context = {**resolved, **peers}
        result[hostname] = SimpleNamespace(**_resolve_pass2(resolved, context))

    return result


def render_config(config_path: str = "dockyman.yaml") -> str:
    config_path = os.path.abspath(config_path)
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config_path_obj = Path(config_path)

    # 1. Tell Jinja where to look for files
    env = Environment(loader=FileSystemLoader(config_path_obj.parent), undefined=StrictUndefined)

    # 2. Inject Ansible inventory hosts as Jinja2 globals (no-op if inventory/ absent)
    env.globals.update(_load_ansible_inventory(config_path_obj.parent))

    # 3. Load the main template
    template = env.get_template(config_path_obj.name)

    # 4. Render
    # it can raise an exception
    render = template.render()

    return render

def load_config(config_path: str = "dockyman.yaml") -> Project:
    """Load *dockyman.yaml* and return a :class:`Project`."""

    render = render_config(config_path)
    raw = yaml.safe_load(render)

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
        dockyman_repo=str(proj_raw["dockyman_repo"]),
        dockyman_ref=str(proj_raw.get("dockyman_ref", "main")),
        swarm=nodes,
        container_log_dir=proj_raw.get("container_log_dir", ""),
        config_log_dir=proj_raw.get("config_log_dir", ""),
    )
    project.base_dir = str(Path(base_dir).resolve())

    # Parse optional ansible: section
    ansible_raw = raw.get("ansible")
    if ansible_raw:
        playbooks = []
        for pb in ansible_raw.get("playbooks", []):
            nodes_val = pb.get("nodes", "all")
            nodes_list = ["all"] if nodes_val == "all" else _to_list(nodes_val)
            playbooks.append(AnsiblePlaybook(
                name=pb["name"],
                file=pb["file"],
                nodes=nodes_list,
                hook=pb.get("hook", ""),
            ))
        project.ansible = AnsibleConfig(
            inventory=ansible_raw["inventory"],
            playbooks=playbooks,
        )
    
    # Backward compatibility: if old 'log_dir' is present, use it for both
    if "log_dir" in proj_raw and proj_raw["log_dir"]:
        old_log_dir = proj_raw["log_dir"]
        if not project.container_log_dir:
            project.container_log_dir = old_log_dir
        if not project.config_log_dir:
            project.config_log_dir = old_log_dir
    
    # Resolve log directories relative to the config file location
    if project.container_log_dir:
        project.container_log_dir = str((Path(project.base_dir) / project.container_log_dir).resolve())
    if project.config_log_dir:
        project.config_log_dir = str((Path(project.base_dir) / project.config_log_dir).resolve())

    return project
