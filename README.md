
# Dockyman v3.0 Documentation

Dockyman is designed to streamline building and deploying Docker containers across multiple nodes. It is particularly suited for scenarios that require mirroring local devices and user/group permissions between the container and the host machine. Dockyman makes it easy to manage containers in a distributed system, ensuring that your applications run with the necessary permissions and access to host resources.

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

The software environment was created and tested on **Ubuntu** operating systems and is recommended for use.

### 1. Install Docker CE

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 2. Configure Docker for Current Non-root User

```bash
sudo usermod -aG docker $USER
```

You may need to log out and log back in for this to take effect.

### 3. Clone and Install Dockyman

```bash
git clone https://github.com/s4hri/dockyman
cd dockyman
make setup 
make install
```

Or install using virtual environments:

```bash
make install
```

Optionally, install to a custom target directory:

```bash
make install TARGET_DIR=~/mycustomdir
```

---

## Getting Started

### Initialize Dockyman Template

Start initializing the template into a specific folder `test`:

```bash
mkdir test
cd test
dockyman init .
```

### Setting up Your Environment

1. Edit `dockyman.yaml` to configure project-specific build/runtime files and the nodes.
2. Define environment variables in `build.env`.

---

### Setting Up SSH Access (Passwordless) for Dockyman Nodes

Dockyman requires passwordless SSH access to all nodes (including localhost) to manage services via Docker Swarm.

#### 1. Check Node Status

```bash
dockyman status
```

If errors occur, verify the following setup steps are completed on **all** nodes:

#### 2. Install SSH Client/Server (if necessary)

```bash
sudo apt-get install openssh-client openssh-server
```

#### 3. Set Up Passwordless SSH Access 

```bash
ssh-copy-id $(whoami)@$(hostname)
```

Repeat this for each remote node (e.g., `ssh-copy-id user@remote-node`).

#### 4. Grant Sudo Access Without Password (Optional)

This step is useful only if you want to use the installation/uninstallation features of dockyman.

```bash
echo "$(whoami) ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/$(whoami)
```

> ⚠️ Use this step carefully; it gives your user full root access without prompting for a password.

For more help, refer to the [Official Documentation on OpenSSH](https://ubuntu.com/server/docs/openssh-server).

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