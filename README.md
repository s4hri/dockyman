# Dockyman

Orchestrate Docker Compose services across multiple machines with built-in hardware, display, and audio management.

Dockyman reads a single `dockyman.yaml` file that describes a **swarm** of nodes (local or remote via SSH), then builds, runs, and tears down containers on every node with one command. Before starting containers it can automatically configure displays (xrandr) and audio (PulseAudio / ALSA) on each node.

## Features

- **Multi-node orchestration** — manage Docker Compose on local and remote (SSH) nodes from one config file.
- **Display management** — list connected displays, auto-detect resolution, or apply custom xrandr settings per node.
- **Audio management** — list devices, set output/input volume, mute/unmute, and run speaker tests (PulseAudio with ALSA fallback).
- **Hardware detection** — collect system, CPU, memory, GPU, audio, USB, network, and disk info per node and save to log files.
- **Per-node logging** — container logs are saved per service (`logs/<node_id>/<service>.log`); hardware logs are saved per node (`logs/<node_id>/config.log`).
- **Dry-run mode** — preview every command without executing it (`--dry-run`).

## Requirements

- Python >= 3.10
- Docker with the Compose plugin (`docker compose`)
- SSH access for remote nodes
- Optional: `xrandr`, `pactl`, `amixer`, `speaker-test` for hardware features

## Installation

```bash
git clone <repo-url>
cd dockyman
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

## Quick start

The `docker/` directory contains a working example with X11 and PulseAudio passthrough.

```bash
cd docker
dockyman build      # build images
dockyman run        # start services, stream logs, press ENTER to stop
```

## Configuration

All settings live in a single `dockyman.yaml` placed next to your Compose files. Use `-f path/to/dockyman.yaml` to point to a different location.

### Node settings reference

| Setting | Description |
|---|---|
| `node_id` | Unique identifier for the node. |
| `compose_file` | Path to the Compose file, relative to `docker_context`. |
| `docker_context` | Directory containing Docker files, relative to `dockyman.yaml`. |
| `docker_host` | Docker daemon socket. Use `ssh://user@host` for remote nodes. |
| `env_file` | Compose `--env-file`, relative to `docker_context`. |
| `build_env_vars` | Shell variables prepended to `docker compose build`. |
| `build_profiles` | Compose profiles activated during build. |
| `build_args` | Extra CLI args appended to the build command. |
| `run_env_vars` | Shell variables prepended to `docker compose up/down/config`. |
| `run_profiles` | Compose profiles activated during run/down/config. |
| `run_args` | Extra CLI args appended to run/down commands (e.g. `--remove-orphans`). |
| `display` | X11 `DISPLAY` value (needed for remote nodes). |
| `display_args` | xrandr arguments (auto-detected if empty). |
| `audio_volume` | Output volume 0–100 (skipped if omitted). |
| `audio_card` | PulseAudio sink name (default sink if empty). |
| `audio_input_volume` | Input volume 0–100 (skipped if omitted). |
| `audio_input_card` | PulseAudio source name (default source if empty). |

## CLI reference

```
dockyman [-f FILE] [--dry-run] <command>
```

### Compose commands

| Command | Description |
|---|---|
| `dockyman status` | Check that all Docker hosts are reachable. |
| `dockyman build` | Build images on all nodes. |
| `dockyman run [-d] [--log-output DIR]` | Apply hardware settings, detect hardware, start services, stream logs, then tear down on ENTER. Use `-d` to detach. |
| `dockyman down` | Stop services on all nodes. |
| `dockyman config` | Show the resolved Compose config for all nodes. |

### Hardware commands

| Command | Description |
|---|---|
| `dockyman info [-n NODE]` | Detect and log hardware information for each node. |
| `dockyman setup` | Apply display and audio settings from `dockyman.yaml`. |

### Audio commands

| Command | Description |
|---|---|
| `dockyman audio list [-n NODE]` | List playback and recording devices. |
| `dockyman audio volume LEVEL [--card SINK] [-n NODE]` | Set output volume (0–100). |
| `dockyman audio input-volume LEVEL [--source SRC] [-n NODE]` | Set input volume (0–100). |
| `dockyman audio mute [--input] [--device DEV] [-n NODE]` | Mute output (or input with `--input`). |
| `dockyman audio unmute [--input] [--device DEV] [-n NODE]` | Unmute output (or input). |
| `dockyman audio test [--card CARD] [-n NODE]` | Run a short speaker test. |

### Display commands

| Command | Description |
|---|---|
| `dockyman display list [-n NODE]` | List connected displays. |
| `dockyman display apply [XRANDR_ARGS] [-n NODE]` | Apply xrandr configuration (auto-detect if omitted). |

All commands that accept `-n NODE` operate on a single node; without it they run on every node in the swarm.

## Logging

- **Container logs** are saved per service under `<log_dir>/<node_id>/<service>.log` (configurable via `log_dir` in `dockyman.yaml` or `--log-output DIR`).
- **Hardware logs** are saved per node as `<log_dir>/<node_id>/config.log` and include the full dockyman configuration and detected hardware (system, CPU, memory, GPU, displays, audio, USB, network, disks).

## X11 and audio troubleshooting

If you see `Authorization required` or `Can't open display` errors, allow Docker access to your X server:

```bash
xhost +local:docker
```

To revoke access later:

```bash
xhost -local:docker
```

## License

MIT — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Istituto Italiano di Tecnologia (IIT) — Davide De Tommaso
