"""Parse and validate dockyman.yaml configuration."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

import yaml

from . import __version__
from jinja2 import Environment, FileSystemLoader, StrictUndefined, UndefinedError


@dataclass
class AnsiblePlaybook:
    """A single Ansible playbook entry."""

    name: str                       # logical name used with --playbook filter
    file: str                       # path to the .yml playbook, relative to dockyman.yaml
    nodes: List[str]                # ["all"] or explicit list of node_ids
    hook: str = ""                  # lifecycle hook: setup (default) | before_build | before_run | after_run | after_down
    extra_vars: dict = field(default_factory=dict)  # passed as --extra-vars to ansible-playbook
    project_scope: bool = False     # True = hosts are defined inside the playbook; no --limit is added


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
    vars_files: List[str] = field(default_factory=list)  # paths to YAML files whose keys are available as template variables
    container_log_dir: str = ""
    config_log_dir: str = ""
    ansible: Optional[AnsibleConfig] = None
    project_playbooks: List[AnsiblePlaybook] = field(default_factory=list)

    # Set after loading – absolute path to the dockyman.yaml directory.
    base_dir: str = ""


def _to_list(value) -> List[str]:
    """Coerce a YAML value (string or list) to a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


_JINJA_RE = re.compile(r'\{\{.*?\}\}', re.DOTALL)


def _escape_jinja(text: str) -> tuple:
    """Replace Jinja2 expressions with safe placeholders for plain YAML parsing.

    Returns (escaped_text, tokens) where tokens holds the original expressions
    in order so they can be restored with :func:`_unescape_jinja`.
    """
    tokens: list = []

    def _sub(m: re.Match) -> str:
        tokens.append(m.group(0))
        return f"__JINJA_{len(tokens) - 1}__"

    return _JINJA_RE.sub(_sub, text), tokens


def _unescape_jinja(value, tokens: list):
    """Recursively restore Jinja2 placeholders in a parsed YAML structure."""
    if isinstance(value, str):
        return re.sub(r'__JINJA_(\d+)__', lambda m: tokens[int(m.group(1))], value)
    if isinstance(value, dict):
        return {k: _unescape_jinja(v, tokens) for k, v in value.items()}
    if isinstance(value, list):
        return [_unescape_jinja(v, tokens) for v in value]
    return value


def _extract_global_vars(text: str) -> Optional[dict]:
    """Extract ``project.vars`` as a flat dict from raw dockyman.yaml text.

    Returns the dict with Jinja2 template strings intact (not yet rendered),
    or ``None`` when ``project.vars`` is absent or not a mapping.
    """
    escaped, tokens = _escape_jinja(text)
    try:
        raw = yaml.safe_load(escaped) or {}
    except yaml.YAMLError:
        return None
    vars_val = (raw.get("project") or {}).get("vars")
    if not isinstance(vars_val, dict):
        return None
    return _unescape_jinja(vars_val, tokens) or None


def _resolve_global_vars(raw_vars: dict, context: dict) -> dict:
    """Render any Jinja2 templates in global var values using *context*.

    Each resolved var is immediately added to the context so that vars
    defined later in the mapping can reference vars defined earlier.
    Values that reference undefined names are left as-is (best-effort).
    """
    _env = Environment(undefined=StrictUndefined)
    resolved = {}
    ctx = dict(context)
    for k, v in raw_vars.items():
        if isinstance(v, str):
            try:
                resolved[k] = _env.from_string(v).render(**ctx)
            except UndefinedError:
                resolved[k] = v
        else:
            resolved[k] = v
        ctx[k] = resolved[k]
    return resolved


def _load_generic_yaml_vars(path: Path) -> dict:
    """Load any YAML file and return its top-level keys as a dict.

    Nested dicts are converted to :class:`~types.SimpleNamespace` so values
    can be accessed with dot notation in Jinja2 templates, e.g.::

        {{ all.hosts.worker.ansible_host }}
        {{ db.host }}

    Non-dict values (strings, lists, numbers) are kept as-is.
    """
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        return {}

    def _to_ns(val):
        if isinstance(val, dict):
            return SimpleNamespace(**{k: _to_ns(v) for k, v in val.items()})
        return val

    return {k: _to_ns(v) for k, v in data.items()}


def _extract_vars_file_paths(text: str, config_dir: Path) -> list[Path]:
    """Extract project.vars_files (or legacy vars_file / inventory) from raw dockyman.yaml.

    Accepts a scalar string or a YAML list.  Returns a (possibly empty) list of
    resolved absolute Paths.
    """
    escaped, tokens = _escape_jinja(text)
    try:
        raw = yaml.safe_load(escaped) or {}
    except yaml.YAMLError:
        return []
    proj = raw.get("project") or {}
    # vars_files (canonical) > vars_file > inventory (legacy)
    raw_val = proj.get("vars_files") or proj.get("vars_file") or proj.get("inventory")
    if not raw_val:
        return []
    # Restore any Jinja placeholders that ended up inside the value
    raw_val = _unescape_jinja(raw_val, tokens)
    entries = raw_val if isinstance(raw_val, list) else [raw_val]
    return [(config_dir / str(e).strip()).resolve() for e in entries if e]


def render_config(config_path: str = "dockyman.yaml") -> str:
    config_path = os.path.abspath(config_path)
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config_path_obj = Path(config_path)

    raw_text = config_path_obj.read_text()

    # 1. Tell Jinja where to look for files (needed for {% import %} / {% include %})
    env = Environment(loader=FileSystemLoader(config_path_obj.parent), undefined=StrictUndefined)

    # 2. Load vars_file(s) and populate Jinja2 globals (later files override earlier ones).
    vars_file_paths = _extract_vars_file_paths(raw_text, config_path_obj.parent)
    env.globals["env"] = os.environ
    for vf_path in vars_file_paths:
        if vf_path.exists():
            env.globals.update(_load_generic_yaml_vars(vf_path))

    # 2b. Extract and resolve project-level global vars ({{ key }} in any field).
    raw_global_vars = _extract_global_vars(raw_text)
    if raw_global_vars:
        env.globals.update(_resolve_global_vars(raw_global_vars, dict(env.globals)))

    # 3. Render the template.
    # Strip YAML comment lines first so that {{ expressions }} inside comments
    # are never evaluated by Jinja2 (they have no effect on the parsed output).
    renderable_text = re.sub(r'^\s*#.*$', '', raw_text, flags=re.MULTILINE)
    template = env.from_string(renderable_text)

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
                playbooks=node_playbooks,
            )
        )

    project = Project(
        name=proj_raw["name"],
        dockyman_repo=str(proj_raw["dockyman_repo"]),
        dockyman_ref=str(proj_raw.get("dockyman_ref", __version__)),
        nodes=node_list,
        vars_files=_to_list(proj_raw.get("vars_files") or proj_raw.get("vars_file") or proj_raw.get("inventory") or []),
        container_log_dir=proj_raw.get("container_log_dir", ""),
        config_log_dir=proj_raw.get("config_log_dir", ""),
    )
    project.base_dir = str(Path(base_dir).resolve())

    # Parse project-level playbooks (hosts defined inside each playbook; no --limit added)
    project_pbs: list[AnsiblePlaybook] = []
    for pb_raw in (proj_raw.get("playbooks") or []):
        project_pbs.append(AnsiblePlaybook(
            name=pb_raw["name"],
            file=pb_raw["file"],
            nodes=[],
            hook=pb_raw.get("hook", ""),
            extra_vars=pb_raw.get("extra_vars") or {},
            project_scope=True,
        ))
    project.project_playbooks = project_pbs

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
