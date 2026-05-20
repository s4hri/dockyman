# Table of Contents

- [Dockyman](#dockyman)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Ansible inventory](#ansible-inventory)
- [CLI reference](#cli-reference)
- [dockyman.yaml Reference](#dockyamanyaml-reference)
- [Logging](#logging)
- [Contributing](#contributing)
  - [Creating a release](#creating-a-release)
  - [Reporting issues](#reporting-issues)
- [License](#license)

---

# Dockyman

[![Python](https://img.shields.io/badge/python-%E2%89%A53.10-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/s4hri/dockyman/ci.yaml?branch=master&label=tests&logo=github&style=flat-square)](https://github.com/s4hri/dockyman/actions/workflows/ci.yaml)

![Dockyman](assets/logo.png?raw=true "Dockyman Logo")

Orchestrate Docker Compose services across multiple machines from a single configuration file.

Dockyman reads a `dockyman.yaml` that describes a **swarm** of nodes (local or remote via SSH) and lets you build, run, and tear down containers on every node with one command. It integrates with an **Ansible inventory** for host variables and can run **Ansible playbooks** automatically as lifecycle hooks (before/after build, run, or teardown).

## Features

- **Multi-node orchestration** — manage `docker compose` on any combination of local and SSH-remote nodes from one config file.
- **Ansible inventory integration** — declare host variables once in `inventory/hosts.yaml`; dockyman and Ansible both read them.
- **Ansible playbook hooks** — run playbooks automatically `before_build`, `before_run`, `after_run`, or `after_down`.
- **Multiple Compose files** — merge several Compose files per node with `-f file1 -f file2 …`.
- **Multiple env files** — pass several `--env-file` paths per node.
- **Hardware detection** — collect system, CPU, memory, GPU, audio, USB, network, and disk info per node; save to a log file or stream to stdout.
- **Per-service container logs** — saved as `<container_log_dir>/<node_id>/<service>.log`.
- **Dry-run mode** — preview every command without executing (`--dry-run`).

## Requirements

- Python ≥ 3.10
- Docker with the Compose plugin (`docker compose`)
- SSH access configured for remote nodes (key-based auth recommended)
- Ansible (optional — only required if `ansible:` block is present in `dockyman.yaml`)

## Installation

```bash
git clone git@github.com:s4hri/dockyman.git
cd dockyman
make install          # creates .venv and installs dockyman
source .venv/bin/activate
```

For development (editable install + activated shell):

```bash
make dev
```

Run the test suite:

```bash
make test
```

## Quick start

```bash
cd example/           # contains a working example
dockyman status       # check Docker daemon reachability on all nodes
dockyman build        # build images on all nodes
dockyman run          # run Ansible hooks, start services, stream logs
```

## Ansible inventory

When an `ansible:` block is present in `dockyman.yaml`, dockyman loads an Ansible inventory and makes host variables available as Jinja2 globals in the config file.

### Directory layout

```
hosts.yaml    ← read by BOTH Ansible and dockyman
vars.yaml     ← dockyman vars only (invisible to Ansible)
```

### `hosts.yaml`

Standard Ansible inventory. Put connection variables and any variables referenced by playbooks here:

```yaml
all:
  vars:
    ansible_python_interpreter: auto_silent   # suppress interpreter-discovery warning
  hosts:
    manager:
      ansible_host:       192.168.1.1
      ansible_connection: local
      volume:             "75%"   # used by configure_audio.yaml
    worker:
      ansible_host: 192.168.1.10
      # ansible_user: myuser     # optional, defaults to current OS user
```

### `vars.yaml`

Dockyman-specific variables — **invisible to Ansible**. Place this file in the same directory as `dockyman.yaml`. Supports Jinja2 templates; `ansible_host`, `ansible_user` (from `hosts.yaml`), and cross-host references (e.g. `{{ worker.ansible_host }}`) are all resolved:

```yaml
manager:
  docker_host:  "unix:///var/run/docker.sock"
  shell_prefix: "PUID=$(id -u) PGID=$(id -g) WORKER_HOST={{ worker.ansible_host }}"

worker:
  docker_host:  "ssh://{{ ansible_user }}@{{ ansible_host }}"
  shell_prefix: "PUID=$(ssh {{ ansible_user }}@{{ ansible_host }} id -u) PGID=$(ssh {{ ansible_user }}@{{ ansible_host }} id -g) MANAGER_HOST={{ manager.ansible_host }}"
```

These variables are then available as Jinja2 globals in `dockyman.yaml`:

```yaml
docker_host: "{{ manager.docker_host }}"
build_shell_prefix: {{ manager.shell_prefix }}
```

> **Rule of thumb:** if a playbook needs it → `hosts.yaml`. If only dockyman needs it → `vars.yaml`.

---

## CLI reference

```
dockyman [-f FILE] [--dry-run] [-V] <command> [options]
```

| Global flag | Description |
|---|---|
| `-f FILE`, `--file FILE` | Path to `dockyman.yaml` (default: `dockyman.yaml` in the current directory). |
| `--dry-run` | Print every command that would be executed without running it. |
| `-V`, `--version` | Print the version and exit. |

---

### `dockyman status`

Check that the Docker daemon on every node is reachable.

```bash
dockyman status
```

---

### `dockyman render`

Render and print the Jinja2-templated `dockyman.yaml` as plain YAML.

```bash
dockyman render
```

---

### `dockyman build`

Run `docker compose build` on every node using `build_shell_prefix`, `build_profiles`, and `build_args`. Runs any playbooks with `hook: before_build` first.

```bash
dockyman build
```

---

### `dockyman run`

The main command. It performs the following steps in order:

1. **Run `before_run` playbooks** (if any are configured).
2. **Log node configuration and hardware info** to `<config_log_dir>/<node_id>.log` (if `config_log_dir` is set).
3. **Start containers** (`docker compose up -d`) on each node.
4. **Run `after_run` playbooks** (if any are configured).
5. **Stream container logs** to stdout, or to `<container_log_dir>/<node_id>/<service>.log` files if logging is configured.
6. **Wait** for the user to press ENTER.
7. **Stop containers** (`docker compose down`) on each node.

```bash
dockyman run                     # interactive: stream logs, press ENTER to stop
dockyman run -d                  # detached: start containers and exit immediately
dockyman run --log-output ./logs # override log directory for this run
```

| Option | Description |
|---|---|
| `-d`, `--detach` | Start containers in the background and exit immediately. |
| `--log-output DIR` | Save container logs to `DIR/<node_id>/<service>.log`. Overrides `container_log_dir` from `dockyman.yaml`. |

---

### `dockyman down`

Stop and remove containers on all nodes (`docker compose down`). Runs any playbooks with `hook: after_down` afterwards.

```bash
dockyman down
```

---

### `dockyman ansible`

Run Ansible playbooks declared in the `ansible:` block of `dockyman.yaml`.

```bash
dockyman ansible                    # run all playbooks
dockyman ansible -p configure_audio # run a specific playbook by name
dockyman ansible -n manager         # limit to a specific node
```

| Option | Description |
|---|---|
| `-p NAME`, `--playbook NAME` | Run only the playbook with this name (default: all). |
| `-n NODE`, `--node NODE` | Limit to a specific node ID. |

---

### `dockyman config`

Print the resolved Compose configuration for each node (`docker compose config`).

```bash
dockyman config                          # all nodes, all profiles
dockyman config --stage build            # build_shell_prefix + build_profiles
dockyman config --stage run              # run_shell_prefix   + run_profiles
dockyman config -n manager               # single node
dockyman config -p build                 # only nodes that have the 'build' profile
dockyman config --stage build -n manager # combine filters
```

| Option | Description |
|---|---|
| `--stage {build,run}` | Apply settings for a specific stage. Default: merge both. |
| `-n NODE`, `--node NODE` | Limit to a specific node ID. |
| `-p PROFILE`, `--profile PROFILE` | Limit to this profile (can be repeated). |

---

### `dockyman info`

Collect and display hardware information for each node: system/OS, CPU, memory, GPU/display, audio, USB devices, network interfaces, and disks.

```bash
dockyman info              # all nodes
dockyman info -n manager   # single node
```

| Option | Description |
|---|---|
| `-n NODE`, `--node NODE` | Limit to a specific node ID. |

---

### `dockyman setup`

Run Ansible playbooks with `hook: setup` (or no hook set) for all nodes.

```bash
dockyman setup
```

---

## dockyman.yaml Reference

All settings live in a single `dockyman.yaml`. Paths are resolved relative to the location of this file. The file is a Jinja2 template — inventory variables are injected automatically as globals.

```yaml
# Optional Ansible integration block (outside project:)
ansible:
  playbooks:
    - name: <string>           # unique name, used with `dockyman ansible -p`
      file: <path>             # path to the playbook, relative to dockyman.yaml
      nodes: all               # "all" or a list of node_ids: [manager, worker]
      hook: before_run         # optional: before_build | before_run | after_run | after_down

project:
  name: <string>
  dockyman_repo: <url>
  dockyman_ref: <string>
  inventory: <path>            # path to the Ansible inventory (hosts.yaml)
  container_log_dir: <path>
  config_log_dir: <path>
  nodes:
    <name>:
      <node settings>
```

### `ansible:` settings

| Setting | Description |
|---|---|
| `playbooks` | List of playbooks to register. Each has `name`, `file`, `nodes`, and optionally `hook`. |

### Playbook hooks

| Hook | Runs |
|---|---|
| `setup` | During `dockyman setup` (default when no hook is set) |
| `before_build` | Before `dockyman build` |
| `before_run` | Before containers start in `dockyman run` |
| `after_run` | After containers start in `dockyman run` |
| `after_down` | After `dockyman down` |

Playbooks without a `hook` run during `dockyman setup` (same as `hook: setup`).

### Project settings

| Setting | Required | Description |
|---|---|---|
| `name` | ✓ | Project name. |
| `dockyman_repo` | ✓ | GitHub repository URL. |
| `dockyman_ref` | | Git tag or branch (defaults to `main`). |
| `inventory` | | Path to the Ansible inventory file (`hosts.yaml`), relative to `dockyman.yaml`. Required when using the `ansible:` block. |
| `container_log_dir` | | Directory for container logs. Omit to stream to stdout. |
| `config_log_dir` | | Directory for hardware/config logs. Omit to stream to stdout. |

### Node settings

| Setting | Required | Description |
|---|---|---|
| `node_id` | ✓ | Unique identifier used in log paths and console output. |
| `compose_files` | ✓ | List of Compose files to merge, relative to `docker_context`. |
| `docker_context` | | Base directory for Docker files. Defaults to the directory of `dockyman.yaml`. |
| `docker_host` | | Docker daemon socket. `unix:///var/run/docker.sock` for local, `ssh://user@host` for remote. |
| `env_files` | | List of env files passed to Compose with `--env-file`. |
| `build_shell_prefix` | | Shell expression prepended to `docker compose build`. |
| `build_profiles` | | Compose profiles activated during `build`. |
| `build_args` | | Extra CLI arguments appended to `docker compose build`. |
| `run_shell_prefix` | | Shell expression prepended to `docker compose up`, `down`, and `config`. |
| `run_profiles` | | Compose profiles activated during `run`, `down`, and `config`. |
| `run_args` | | Extra CLI arguments appended to `docker compose up` and `down`. |

## Logging

| File | When written | Contents |
|---|---|---|
| `<config_log_dir>/<node_id>.log` | `dockyman info`, `dockyman run` | Node configuration + full hardware scan. |
| `<container_log_dir>/<node_id>/<service>.log` | `dockyman run` (when `container_log_dir` is set) | Live container log output for that service. |

Both logging types are **off by default** — output streams to stdout when the corresponding directory is not set.

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository and create your branch from `master`:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Set up** a development environment:
   ```bash
   make dev
   ```

3. **Make your changes** and ensure the test suite passes:
   ```bash
   make test
   ```

4. **Add tests** for any new behaviour. Tests live in `tests/` and are run with `pytest`.

5. **Open a Pull Request** against `master`. The CI pipeline runs automatically.

### Creating a release

The package version is derived automatically from git tags via `setuptools-scm`. To cut a new release:

1. **Ensure `master` is clean and all tests pass:**
   ```bash
   make test
   ```

2. **Create and push an annotated tag:**
   ```bash
   git tag -a v4.4.0 -m "Release v4.4.0"
   git push origin v4.4.0
   ```

   The tag must follow the `vMAJOR.MINOR.PATCH` format. Once pushed, the CI pipeline
   will pick up the new tag and the installed package will report that version via
   `dockyman -V`.

3. **Reinstall locally** if you want to verify the version in your dev environment:
   ```bash
   pip install -e .
   dockyman -V
   ```

---

### Reporting issues

Please open a GitHub issue including:
- dockyman version (`dockyman -V`)
- OS and Python version
- Minimal `dockyman.yaml` that reproduces the problem
- Full error output

---

## License

MIT — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Istituto Italiano di Tecnologia (IIT) — Davide De Tommaso
