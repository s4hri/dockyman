
# Dockyman v2.4 Documentation

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
   - [dockyman.env](#customizing-dockymanenv)
   - [nodes.yaml](#customizing-nodesyaml)
   - [compose.yaml](#customizing-composeyaml)
   - [base/compose.yaml](#customizing-basecomposeyaml)
   - [local/compose.yaml](#customizing-localcomposeyaml)
6. [Commands](#commands)
   - [Status](#status-command)
   - [Setup](#setup-command)
   - [Build](#build-command)
   - [Pull](#pull-command)
   - [Push](#push-command)
   - [Run](#run-command)
   - [Stop](#stop-command)
7. [Best Practices](#best-practices)
   - [Security Considerations](#security-considerations)
   - [Managing Node Configurations](#managing-node-configurations)
   - [Logging and Error Handling](#logging-and-error-handling)
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

- **`dockyman.env`**: Contains environment variables used throughout the Dockyman configuration.
- **`nodes.yaml`**: Defines the Docker Swarm configuration, including manager and worker nodes.
- **`compose.yaml`**: Main Docker Compose file orchestrating services across nodes.
- **`base/compose.yaml`**: Docker Compose file for building the base Docker image(s).
- **`local/compose.yaml`**: Docker Compose file for building the local Docker image(s).
- **`base/Dockerfile`** and **`local/Dockerfile`**: Define the Dockerfiles for building base and local images.

---

## Installation

To install Dockyman, run the following commands:

```bash
git clone https://github.com/s4hri/dockyman
git checkout v2.x
cd dockyman
cd dockyman/model/.dockyman_installer
bash install.sh
```

Alternatively, use the script: (NOT YET AVAILABLE!)

```bash
sh -c 'curl -O https://raw.githubusercontent.com/s4hri/dockyman/v2.0/dockyman/model/.dockyman_installer/dockyman.sh && sudo mv dockyman.sh /usr/local/bin/dockyman'
```

---

## Getting Started

### Setting Up SSH Access (Passwordless) for Dockyman Nodes

Before starting with Dockyman, it is essential to configure SSH access without a password between the host machine and all machines defined in `nodes.yaml`. This is required for Dockyman to manage nodes seamlessly.

Follow these steps to set up passwordless SSH access:

1. **Generate an SSH Key Pair** (if you don’t already have one):

   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   ```

   - When prompted, press Enter to accept the default file location (`~/.ssh/id_rsa`).
   - Leave the passphrase empty for passwordless access.

2. **Copy the Public Key to Each Node**:

   For each machine defined in `nodes.yaml`, copy the public key to the authorized keys list using `ssh-copy-id`:

   ```bash
   ssh-copy-id user@node-ip-address
   ```

   Replace `user` with the SSH username and `node-ip-address` with the machine’s IP address defined in `nodes.yaml`.

3. **Verify Passwordless Access**:

   Test the connection to ensure that you can access each machine without being prompted for a password:

   ```bash
   ssh user@node-ip-address
   ```

   If you are not prompted for a password, the setup is complete.

---

### Note:
- Ensure the same SSH key is used for all nodes.
- Avoid exposing private keys to public repositories.
- If `ssh-copy-id` is not available, manually append the contents of your `~/.ssh/id_rsa.pub` to the `~/.ssh/authorized_keys` file on each node.

---

### Initialize Dockyman Template

From the directory of your repository, run:

```bash
dockyman init .
```

### Setting up Your Environment

1. **Set Up Environment Variables**: Customize the `dockyman.env` file to match your environment’s needs.
2. **Configure Nodes**: Define the manager and worker nodes in the `nodes.yaml` file.
3. **Prepare Docker Compose Files**: Edit `compose.yaml`, `base/compose.yaml`, and `local/compose.yaml` to configure your services.

## Configuration

### dockyman.env

Customize this file to set environment variables such as base image sources, user/group configurations, and project names.

### nodes.yaml

Defines the network configuration for manager and worker nodes.

### compose.yaml

Main Docker Compose file orchestrating services across nodes.

### base/compose.yaml and local/compose.yaml

Customize these files for building base and local Docker images during the building process.

---

## Commands

### Status Command

Check the status of nodes and SSH connections:

```bash
dockyman status
```

### Setup Command

Check, install, or uninstall required software:

```bash
dockyman setup check
```

### Build Command

Build the base and local Docker images:

```bash
dockyman build
```

### Pull Command

Pull Docker base images:

```bash
dockyman pull
```

### Push Command

Push Docker base images to a registry:

```bash
dockyman push
```

### Run Command

Deploy the local images:

```bash
dockyman run
```

### Stop Command

Stop running services:

```bash
dockyman stop
```

---

## Best Practices

### Security Considerations

- Use Docker secrets for sensitive data.
- Ensure Docker containers run with correct user permissions.

### Managing Node Configurations

- Regularly test SSH and Docker daemon connectivity.
- Consider dynamic configuration automation if your environment is highly dynamic.

### Logging and Error Handling

- Implement centralized logging for easier monitoring.
- Set up alerts for critical errors during Docker operations.

---

## Contributing

We welcome contributions! Follow these steps to contribute:

1. Fork the repository.
2. Clone your fork.
3. Create a new branch.
4. Make changes and test them.
5. Push your changes and submit a pull request.

---

## Support

If you encounter issues, refer to the [GitHub repository](https://github.com/s4hri/dockyman) to open an issue or browse the documentation.

---

## License

Dockyman is licensed under the [MIT License](https://github.com/s4hri/dockyman/LICENSE).
