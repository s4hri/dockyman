"""Parse and validate dockyman.yaml configuration."""

from __future__ import annotations

import getpass
import os
import re
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
    extra_vars: dict = field(default_factory=dict)  # passed as --extra-vars to ansible-playbook


@dataclass
class AnsibleConfig:
    """Top-level ansible: section from dockyman.yaml."""

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

    # Ansible playbooks scoped to this node; run with --limit <node_id> automatically.
    playbooks: List[AnsiblePlaybook] = field(default_factory=list)

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
    nodes: List[Node]
    inventory: str = ""            # path to the Ansible inventory file, relative to dockyman.yaml
    container_log_dir: str = ""
    config_log_dir: str = ""
    ansible: Optional[AnsibleConfig] = None

    # Set after loading – absolute path to the dockyman.yaml directory.
    base_dir: str = ""

    @property
    def swarm(self) -> List[Node]:
        """Backward-compatible alias for :attr:`nodes`."""
        return self.nodes


def _to_list(value) -> List[str]:
    """Coerce a YAML value (string or list) to a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _load_vars_file(config_dir: Path) -> Optional[dict]:
    """Load ``vars.yaml`` from the same directory as ``dockyman.yaml``.

    Returns the parsed dict, or ``None`` when the file does not exist.
    """
    vars_file = config_dir / "vars.yaml"
    if not vars_file.exists():
        return None
    data = yaml.safe_load(vars_file.read_text()) or {}
    return data if isinstance(data, dict) else None


def _extract_inventory_path(text: str, config_dir: Path) -> Optional[Path]:
    """Extract project.inventory from raw dockyman.yaml text.

    Returns the resolved absolute Path to the inventory file, or None if not
    found.
    """
    in_project = False
    for line in text.splitlines():
        stripped = line.rstrip()
        if re.match(r'^project\s*:', stripped):
            in_project = True
            continue
        if in_project:
            if stripped and not stripped[0].isspace() and not stripped.startswith('#'):
                break
            m = re.match(r'^\s+inventory\s*:\s*(.+)', stripped)
            if m:
                val = m.group(1).strip().strip('"\'')
                return (config_dir / val).resolve()
    return None


def _load_ansible_inventory(
    config_dir: Path,
    *,
    hosts_file: Optional[Path] = None,
    inline_vars: Optional[dict] = None,
) -> dict[str, SimpleNamespace]:
    """Return {hostname: SimpleNamespace} from the Ansible inventory if present.

    Reads two sources and merges them (later sources win):
      1. The inventory file pointed to by ``project.inventory`` (or
         ``inventory/hosts.yaml`` as a fallback) — per-host ansible_host /
         ansible_user / etc.
      2. ``vars:`` section in dockyman.yaml (preferred) or inventory/vars.yaml
         (fallback) — 'all:' block for shared defaults, then per-host blocks.

    String values are resolved as Jinja2 templates iteratively so vars can
    reference each other (e.g. docker_host can embed ansible_host).

    Falls back to an empty dict when the inventory file does not exist.
    """
    if hosts_file is not None:
        inv_dir = hosts_file.parent
        actual_hosts_file = hosts_file
    else:
        inv_dir = config_dir / "inventory"
        actual_hosts_file = inv_dir / "hosts.yaml"

    if not inv_dir.is_dir():
        return {}

    # 1. Per-host ansible vars from the inventory file (ansible_host, ansible_connection, …)
    hosts_ansible_vars: dict[str, dict] = {}
    if actual_hosts_file.exists():
        hosts_data = yaml.safe_load(actual_hosts_file.read_text()) or {}
        for group in hosts_data.values():
            for hostname, hvars in (group.get("hosts") or {}).items():
                hosts_ansible_vars[hostname] = hvars or {}

    # 2. host-specific vars: inline vars: section in dockyman.yaml takes
    #    precedence; falls back to inventory/vars.yaml when absent.
    group_all: dict = {}
    host_vars: dict[str, dict] = {}
    if inline_vars is not None:
        raw_vars = dict(inline_vars)
    else:
        vars_file = inv_dir / "vars.yaml"
        raw_vars = yaml.safe_load(vars_file.read_text()) if vars_file.exists() else {}
        raw_vars = raw_vars or {}
    group_all = raw_vars.pop("all", {}) or {}
    host_vars = {k: v or {} for k, v in raw_vars.items()}

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

    raw_text = config_path_obj.read_text()

    # 1. Tell Jinja where to look for files (needed for {% import %} / {% include %})
    env = Environment(loader=FileSystemLoader(config_path_obj.parent), undefined=StrictUndefined)

    # 2. Load vars.yaml and inventory, then populate Jinja2 globals.
    vars_data = _load_vars_file(config_path_obj.parent)
    hosts_file = _extract_inventory_path(raw_text, config_path_obj.parent)
    env.globals.update(_load_ansible_inventory(
        config_path_obj.parent,
        hosts_file=hosts_file,
        inline_vars=vars_data,
    ))

    # 3. Render the template.
    template = env.from_string(raw_text)

    return template.render()

def load_config(config_path: str = "dockyman.yaml") -> Project:
    """Load *dockyman.yaml* and return a :class:`Project`."""

    render = render_config(config_path)
    raw = yaml.safe_load(render)

    proj_raw = raw["project"]
    base_dir = os.path.dirname(config_path)

    node_list: list[Node] = []
    # Accept nodes: as a mapping {name: attrs} (current) or
    # a list [{node_id: name, ...}] / swarm: (backward compat).
    raw_nodes = proj_raw.get("nodes") or proj_raw.get("swarm", [])
    if isinstance(raw_nodes, dict):
        nodes_iter = [(nid, nattrs or {}) for nid, nattrs in raw_nodes.items()]
    else:
        nodes_iter = [(n["node_id"], n) for n in raw_nodes]
    for node_id, node_raw in nodes_iter:
        node_playbooks: list[AnsiblePlaybook] = []
        for pb_raw in (node_raw.get("playbooks") or []):
            nodes_val = pb_raw.get("nodes", node_id)
            pb_nodes = ["all"] if nodes_val == "all" else _to_list(nodes_val)
            node_playbooks.append(AnsiblePlaybook(
                name=pb_raw["name"],
                file=pb_raw["file"],
                nodes=pb_nodes,
                hook=pb_raw.get("hook", ""),
                extra_vars=pb_raw.get("extra_vars") or {},
            ))
        node_list.append(
            Node(
                node_id=node_id,
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
                playbooks=node_playbooks,
            )
        )

    project = Project(
        name=proj_raw["name"],
        dockyman_repo=str(proj_raw["dockyman_repo"]),
        dockyman_ref=str(proj_raw.get("dockyman_ref", "main")),
        nodes=node_list,
        inventory=proj_raw.get("inventory", ""),
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
