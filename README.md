# Table of Contents

- [Dockyman](#dockyman)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [dockyman.yaml.j2 Reference](#dockyman-configuration-file-reference)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)

---

# Dockyman

[![Python](https://img.shields.io/badge/python-%E2%89%A53.10-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/s4hri/dockyman/ci.yml?branch=master&label=tests&logo=github&style=flat-square)](https://github.com/s4hri/dockyman/actions/workflows/ci.yml)

![Dockyman](assets/logo.png?raw=true "Dockyman Logo")

Orchestrate Docker Compose services across multiple machines from a single configuration file.

Dockyman reads a `dockyman.yaml.j2` that describes a **swarm** of nodes (local or remote via SSH) and lets you build, run, and tear down containers on every node with one command. Before starting containers it can run a `setup_script` on each node to configure the environment (display, audio, env vars, etc.) and silently collect hardware information into a log file.

## Features

- **Multi-node orchestration** — manage `docker compose` on any combination of local and SSH-remote nodes from one config file.
- **Multiple Compose files** — merge several Compose files per node with `-f file1 -f file2 …`.
- **Multiple env files** — pass several `--env-file` paths per node.
- **Per-node setup script** — run arbitrary shell commands on each node before containers start (xrandr, pactl, env exports, etc.).
- **Hardware detection** — collect system, CPU, memory, GPU, audio, USB, network, and disk info per node; save to a log file or stream to stdout.
- **Per-service container logs** — saved as `<container_log_dir>/<node_id>/<service>.log`.
- **Dry-run mode** — preview every command without executing (`--dry-run`).

## Requirements

- Python ≥ 3.10
- Docker with the Compose plugin (`docker compose`)
- SSH access configured for remote nodes (key-based auth recommended)

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
cd docker/                # contains a working example
dockyman info             # inspect node configuration and hardware
dockyman build            # build images on all nodes
dockyman run              # start services, stream logs, press ENTER to stop
```

## CLI reference

```
dockyman [-f FILE] [--dry-run] [-V] <command> [options]
```

| Global flag | Description |
|---|---|
| `-f FILE`, `--file FILE` | Path to `dockyman.yaml.j2` (default: `dockyman.yaml.j2` in the current directory). |
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

Render and print the configuration file converted from Jinja to YAML.

```bash
dockyman render
```

---

### `dockyman build`

Run `docker compose build` on every node using `build_shell_prefix`, `build_profiles`, and `build_args`.

```bash
dockyman build
```

---

### `dockyman run`

The main command. It performs the following steps in order:

1. **Run `setup_script`** on each node (silently — output is not shown).
2. **Log node configuration and hardware info** to `<config_log_dir>/<node_id>.log` (if `config_log_dir` is set). The node configuration (compose files, env files, shell prefixes, etc.) is also printed to the console.
3. **Start containers** (`docker compose up -d`) on each node.
4. **Stream container logs** to stdout, or to `<container_log_dir>/<node_id>/<service>.log` files if logging is configured.
5. **Wait** for the user to press ENTER.
6. **Stop containers** (`docker compose down`) on each node.

```bash
dockyman run                     # interactive: stream logs, press ENTER to stop
dockyman run -d                  # detached: start containers and exit immediately
dockyman run --log-output ./logs # override log directory for this run
```

| Option | Description |
|---|---|
| `-d`, `--detach` | Start containers in the background and exit immediately. |
| `--log-output DIR` | Save container logs to `DIR/<node_id>/<service>.log`. Overrides `container_log_dir` from `dockyman.yaml.j2`. |

---

### `dockyman down`

Stop and remove containers on all nodes (`docker compose down`).

```bash
dockyman down
```

---

### `dockyman config`

Print the resolved Compose configuration for each node (`docker compose config`).

```bash
dockyman config
```

---

### `dockyman info`

Collect and display hardware information for each node: system/OS, CPU, memory, GPU/display, audio, USB devices, network interfaces, and disks. Also prints the full node configuration (compose files, prefixes, setup script, etc.).

- If `config_log_dir` is set: output is captured silently and saved to `<config_log_dir>/<node_id>.log`. The saved path is printed to the console.
- If `config_log_dir` is empty: all output is streamed live to stdout.

```bash
dockyman info              # all nodes
dockyman info -n manager   # single node
```

| Option | Description |
|---|---|
| `-n NODE`, `--node NODE` | Limit to a specific node ID. |

---

### `dockyman setup`

Run `setup_script` interactively on each node (local shell or via SSH for remote nodes). Use this to apply display, audio, or environment settings independently from `dockyman run`.

```bash
dockyman setup
```

---

## Dockyman configuration file reference

All settings live in a single `dockyman.yaml.j2` configuration file. Paths are resolved relative to the location of this file unless noted otherwise.

```yaml
project:
  name: <string>               # Project name (required)
  dockyman_repo: <url>         # GitHub repo URL (required)
  dockyman_ref: <string>        # Tag or branch (optional, default: main)
  container_log_dir: <path>    # Container logs directory (optional, see below)
  config_log_dir: <path>       # Hardware/config logs directory (optional, see below)
  swarm:
    - <node>
    - <node>
```

### Project settings

| Setting | Required | Description |
|---|---|---|
| `name` | ✓ | Project name. |
| `dockyman_repo` | ✓ | GitHub repository URL for this dockyman project. |
| `dockyman_ref` | | Git tag or branch to track (defaults to `main`). |
| `container_log_dir` | | Directory for container logs, relative to `dockyman.yaml.j2` or absolute. Omit or leave empty (default) to stream container logs to stdout. |
| `config_log_dir` | | Directory for hardware/config logs, relative to `dockyman.yaml.j2` or absolute. Omit or leave empty (default) to stream hardware info to stdout. |
| `log_dir` | | **Deprecated.** Use `container_log_dir` and `config_log_dir` instead. When present, sets both directories for backward compatibility. |

### Node settings

Each entry in `swarm` describes one node.

| Setting | Required | Description |
|---|---|---|
| `node_id` | ✓ | Unique identifier used in log paths and console output. |
| `compose_files` | ✓ | List of Compose files to merge, relative to `docker_context`. Passed as `-f file1 -f file2 …`. A single string is also accepted. |
| `docker_context` | | Base directory for Docker files, relative to `dockyman.yaml.j2`. Defaults to `""` (same directory as the yaml file). |
| `docker_host` | | Docker daemon socket. Use `unix:///var/run/docker.sock` for local, `ssh://user@host` for remote. Injected as `DOCKER_HOST=…` in every command. |
| `env_files` | | List of env files passed to Compose with `--env-file`, relative to `docker_context`. A single string is also accepted. |
| `build_shell_prefix` | | Shell expression prepended to `docker compose build` (e.g. `PUID=$(id -u) PGID=$(id -g)`). |
| `build_profiles` | | List of Compose profiles activated during `build`. |
| `build_args` | | Extra CLI arguments appended to `docker compose build` (e.g. `--no-cache`). |
| `run_shell_prefix` | | Shell expression prepended to `docker compose up`, `down`, and `config`. |
| `run_profiles` | | List of Compose profiles activated during `run`, `down`, and `config`. |
| `run_args` | | Extra CLI arguments appended to `docker compose up` and `down` (e.g. `--remove-orphans`). |
| `setup_script` | | Multi-line shell script executed directly on the node (locally or via SSH). Run interactively by `dockyman setup`; run silently before containers start by `dockyman run`. |

## Logging

| File | When written | Contents |
|---|---|---|
| `<config_log_dir>/<node_id>.log` | `dockyman info`, `dockyman run` | Node configuration (compose files, env files, shell prefixes, setup script) + full hardware scan (OS, CPU, memory, GPU, audio, USB, network, disks). |
| `<container_log_dir>/<node_id>/<service>.log` | `dockyman run` (when `container_log_dir` is set) | Live container log output for that service. |

All logging is **OFF by default**:
- When `container_log_dir` is empty or omitted: container logs are streamed to stdout.
- When `config_log_dir` is empty or omitted: `dockyman info` streams hardware output to stdout.
- You can enable each type of logging independently or disable both.

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository and create your branch from `v4.x`:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Set up** a development environment:
   ```bash
   make dev   # installs in editable mode and opens an activated shell
   ```

3. **Make your changes** and ensure the test suite passes:
   ```bash
   make test
   ```

4. **Add tests** for any new behaviour. Tests live in `tests/` and are run with `pytest`.

5. **Open a Pull Request** against the `v4.x` branch. The CI pipeline will run automatically — PRs can only be merged when all tests pass.

### Code style

- Python 3.10+, type annotations encouraged.
- Keep public functions documented with docstrings.
- Follow the existing module structure (`config`, `executor`, `hardware`, `runner`, `logger`, `cli`).

### Reporting issues

Please open a GitHub issue including:
- dockyman version (`dockyman -V`)
- OS and Python version
- Minimal `dockyman.yaml.j2` that reproduces the problem
- Full error output

---

## License

MIT — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Istituto Italiano di Tecnologia (IIT) — Davide De Tommaso
