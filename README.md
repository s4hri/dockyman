
# Dockyman v2.2

Dockyman is a powerful tool designed to streamline building and deploying of Docker containers across multiple nodes. Dockyman suits specifically for scenarios that require mirroring local devices and user/group permissions between the container and the host machine. It allows you to easily manage containers in a distributed system, ensuring that your applications run with the necessary permissions and access to host resources.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Usage](#usage)
   - [Building Images](#building-images)
   - [Deploying Services](#deploying-services)
   - [Managing Services](#managing-services)
6. [Configuration](#configuration)
7. [Contributing](#contributing)
   - [How to Contribute](#how-to-contribute)
8. [Support](#support)
9. [License](#license)

## Overview

Dockyman is designed for managing Docker environments across multiple nodes with ease. It provides a simple way to build and deploy containers, especially for setups requiring specific user permissions, graphical applications, or audio processing. Dockyman is ideal for distributed systems where containers must interact closely with the host machine.

## Features

- **Multi-node management**: Easily configure and manage Docker Swarm across multiple nodes.
- **Host integration**: Mirrors local user/group permissions and devices within Docker containers.
- **Graphical and audio application support**: Seamlessly run applications that require access to X11, PulseAudio, and NVIDIA GPUs.
- **Customizable deployment**: Extensive configuration options via Docker Compose files and environment variables.
- **Centralized control**: Manage builds, deployments, and services from a single command line interface.

Examples of use cases are:

- Running graphical applications using the X11 server running in the host machine.
- Running applications using GPUs capabilities of the host machine (NVIDIA supported).
- Running audio applications using PulseAudio server running in the host machine.
- Using custom bash scripts to run before/after the container has started.
- Using containers with a non-root user having the same UIDs/GIDs of the current logged user in the host machine.
- Using containers with non-root user with specific group permissions (sudo, audio, video, ...) with the same GIDs of the host machine.

## Installation

To install Dockyman, you can use the following command:

```bash
sh -c 'curl -O https://raw.githubusercontent.com/s4hri/dockyman/v2.0/dockyman/model/.dockyman_installer/dockyman.sh && sudo mv dockyman.sh /usr/local/bin/dockyman'
```

This command will download the `dockyman.sh` script, make it executable, and move it to `/usr/local/bin/` for easy access.

## Getting Started

### Initialize Dockyman Template

From the directory of your repository you will be able to initialize the Dokyman Template with the following command:

```bash
dockyman init .
```

### Setting-up your Environment

1. **Set Up Environment Variables**:
   Customize the `dockyman.env` file to match your environment’s needs, including setting up base image sources, user/group configurations, and project names.

2. **Configure Nodes**:
   Define the manager and worker nodes in the `nodes.yaml` file, specifying IP addresses, SSH users, and Docker daemon addresses.

3. **Prepare Docker Compose Files**:
   Edit the `compose.yaml`, `base/compose.yaml`, and `local/compose.yaml` files to configure your services and ensure they are set up correctly for both building and deploying.

## Usage

### Building Images

To build the base and local Docker images, use the following command:

```bash
dockyman build
```

This command builds the Docker images as defined in your `base/compose.yaml` and `local/compose.yaml` files.

### Deploying Services

To deploy your services across the Docker Swarm, use the command:

```bash
dockyman run
```

This command uses the `compose.yaml` file to deploy services to the manager and worker nodes specified in `nodes.yaml`.

### Managing Services

To stop all running services, use:

```bash
dockyman stop
```

This command stops all services deployed by Dockyman, bringing down the containers while preserving their data.

## Configuration

For more detailed configuration instructions, please refer to the [Dockyman Template v2.0 Documentation](./dockyman/model/README.md).


## Contributing

We welcome contributions to the Dockyman project! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### How to Contribute

1. **Fork the Repository**: Start by forking the Dockyman repository on GitHub.
2. **Clone Your Fork**: Clone your forked repository to your local machine:
   ```bash
   git clone https://github.com/your-username/dockyman.git
   ```
3. **Create a Branch**: Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make Changes**: Make your changes, and be sure to test them thoroughly.
5. **Commit and Push**: Commit your changes and push them to your forked repository:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/your-feature-name
   ```
6. **Submit a Pull Request**: Open a pull request on the original Dockyman repository with a description of your changes.

## Support

If you encounter any issues or need help, please visit our [GitHub repository](https://github.com/s4hri/dockyman) to open an issue or browse the documentation.

## License

Dockyman is licensed under the [MIT License](https://github.com/s4hri/dockyman/LICENSE).