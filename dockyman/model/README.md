# Dockyman v3.0 Documentation

Dockyman is designed to streamline building and deploying Docker containers across multiple nodes. It is particularly suited for scenarios that require mirroring local devices and user/group permissions between the container and the host machine. Dockyman makes it easy to manage containers in a distributed system, ensuring that your applications run with the necessary permissions and access to host resources.

## Table of Contents

1. [Overview](#overview)
2. [Folder Structure](#folder-structure)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
   - [Initialize Dockyman Template](#initialize-dockyman-template)
   - [Setting up Your Environment](#setting-up-your-environment)
   - [Setting Up SSH Access (Passwordless) for Dockyman Nodes](#setting-up-ssh-access-passwordless-for-dockyman-nodes)
5. [Configuration](#configuration)
   - [dockyman.yaml](#dockymanyaml)
   - [build.env](#buildenv)
6. [Commands](#commands)
   - [Build](#build-command)
   - [Pull](#pull-command)
   - [Push](#push-command)
   - [Run](#run-command)
   - [Stop](#stop-command)
   - [Clean](#clean-command)
7. [Best Practices](#best-practices)
8. [Contributing](#contributing)
9. [Support](#support)
10. [License](#license)

---

## Overview

Dockyman is designed for managing Docker environments across multiple nodes with ease. It provides a simple way to build and deploy containers, especially for setups requiring specific user permissions, graphical applications, or audio processing. Dockyman is ideal for distributed systems where containers must interact closely with the host machine.

### Features

- **Multi-node management**: Easily configure and manage Docker Swarm across multiple nodes.
- **Host integration**: Mirrors local user/group permissions and devices within Docker containers.
- **Graphical and audio application support**: Seamlessly run applications that require access to X11, PulseAudio, and NVIDIA GPUs.
- **Customizable deployment**: Extensive configuration options via Docker Compose files and environment variables.
- **Centralized control**: Manage builds, deployments, and services from a single command-line interface.

---

## Folder Structure

- **`dockyman.yaml`**: Central configuration file for project build and runtime.
- **`build.env`**: Environment variables used during the image build process.
- **`compose.yaml`**: Main Docker Compose file for runtime.
- **`base/compose.yaml`**: Compose file for base image builds.
- **`local/compose.yaml`**: Compose file for local image builds.

---

## Installation

```bash
git clone https://github.com/s4hri/dockyman
git checkout v3.0
cd dockyman
cd dockyman/model/.dockyman_installer
bash install.sh
```

---

## Getting Started

### Initialize Dockyman Template
As first entrypoint, you can start initializing the template into a specific folder `test`:

```bash
mkdir test
cd test
dockyman init .
```

### Setting up Your Environment

1. Edit `dockyman.yaml` to set up project-specific build/runtime files and configuring the nodes.
2. Define environment variables in `build.env`.

---

### Setting Up SSH Access (Passwordless) for Dockyman Nodes

Follow standard SSH key generation and `ssh-copy-id` process to ensure passwordless SSH access between manager and worker nodes.

---

## Configuration

### dockyman.yaml

Main configuration file for:
- Build config (base/local)
- Runtime config
- Swarm nodes
- Additional environments

### build.env

Used during builds. Includes:
- Image tags
- User/group settings
- Profiles for compose

---

## Commands

### Build Command

Build base and local images:

```bash
dockyman build
```

### Pull Command

Pull base images:

```bash
dockyman pull
```

### Push Command

Push base images:

```bash
dockyman push
```

### Run Command

Run services on the swarm nodes:

```bash
dockyman run
```

### Stop Command

Stop and bring down services:

```bash
dockyman stop
```

### Clean Command

Remove containers and images:

```bash
dockyman clean
```

---

## Best Practices

- Use `.env` files carefully and securely.
- SSH into nodes to test permissions and Docker socket access.
- Use `DOCKER_LOGS=true` in your env file to enable automatic log streaming.

---

## Contributing

Feel free to fork, branch, and submit pull requests!

---

## Support

For help, submit an issue via the [GitHub repository](https://github.com/s4hri/dockyman/issues).

---

## License

Licensed under the [MIT License](https://github.com/s4hri/dockyman/blob/main/LICENSE).