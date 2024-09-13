
# Dockyman Template v2.0 Documentation

This documentation will guide you through customizing, expanding, and managing your `dockyman` setup. The `dockyman` tool is designed to streamline Docker management, especially for environments that require mirroring local devices and user/group permissions between the container and the host machine.

## Table of Contents

1. [Overview](#overview)
2. [Folder Structure](#folder-structure)
3. [Getting Started](#getting-started)
4. [Customizing the Configuration](#customizing-the-configuration)
   - [dockyman.env](#customizing-dockymanenv)
   - [nodes.yaml](#customizing-nodesyaml)
   - [compose.yaml](#customizing-composeyaml)
   - [base/compose.yaml](#customizing-basecomposeyaml)
   - [local/compose.yaml](#customizing-localcomposeyaml)
5. [Commands](#commands)
   - [Status Command](#status-command)
   - [Setup Command](#setup-command)
   - [Build Command](#build-command)
   - [Pull Command](#pull-command)
   - [Push Command](#push-command)
   - [Run Command](#run-command)
   - [Stop Command](#stop-command)
6. [Best Practices](#best-practices)
   - [Security Considerations](#security-considerations)
   - [Managing Node Configurations](#managing-node-configurations)
   - [Logging and Error Handling](#logging-and-error-handling)
7. [Support](#support)

## Overview

Dockyman simplifies the management of Docker environments across multiple nodes, ensuring that containerized applications can run with the necessary permissions and access to host resources. This template provides a starting point for configuring and deploying your dockyman Docker environments.

## Folder Structure

- **`dockyman.env`**: Contains environment variables used throughout the Dockyman configuration.
- **`nodes.yaml`**: Defines the Docker Swarm configuration, including the manager and worker nodes.
- **`compose.yaml`**: Main Docker Compose file orchestrating services across nodes.
- **`base/compose.yaml`**: Docker Compose file for building the base Docker image(s).
- **`base/Dockerfile`**: Dockerfile referred in the Docker Compose for building base image(s).
- **`local/compose.yaml`**: Docker Compose file for building the local Docker image(s).
- **`local/Dockerfile`**: Dockerfile referred in the Docker Compose for building local image(s).

## Getting Started

1. **Install Dockyman**:
   ```bash
      sh -c 'curl -O https://s4hri/dockyman/dockyman/model/.dockyman_installer/dockyman.sh && chmod +x dockyman.sh && sudo mv dockyman.sh /usr/local/bin/dockyman'
   ```

2. **Set Up Environment Variables**:
   Review and customize the `dockyman.env` file to fit your environment.

3. **Configure Nodes**:
   Update `nodes.yaml` with your network configuration, including manager and worker nodes. If your application runs in a non-distributed system, but instead on a single local machine, you do not need to update this file.

4. **Configure your Base Docker Images**:
   Update the `base/compose.yaml` services that will build Base Docker Images during the building process.

   **Key Points:**
   - `image:` Defines the base image name.
   - `build:` Specifies the context, Dockerfile, and build arguments.
   - `dockyman.node:` Indicates which nodes this build should apply to (nodes are defined in `nodes.yaml`).

5. **Configure your Local Docker Images**:
   Update the `local/compose.yaml` services that will build Local Docker Images during the building process.

   **Key Points:**
   - `image:` Defines the base image name.
   - `build:` Customizes the image build to match the user and group configurations of the host.
   - `dockyman.node:` As with the base image, this section specifies which nodes the service applies to.

6. **Configure the Main Compose File**:
   Update the `compose.yaml` services that will run Local Docker Images during the deployment process.

   **Key Points:**
   - `image:` Defines the base image name.
   - `build:` Specifies the context, Dockerfile, and build arguments.
   - `dockyman.node:` Indicates which nodes this build should apply to (nodes are defined in `nodes.yaml`).

7. **Build Docker Images**:
   Run the following commands to build the base and local images:
   ```bash
   dockyman build
   ```

8. **Deploy the Services**:
   Deploy your services using Docker Compose:
   ```bash
   dockyman run
   ```

## Commands

### Status Command

The `status` command is used to check the status of your nodes and specifically SSH connections.

```bash
dockyman status [nodes_file]
```

- **nodes_file**: Optional. The path to the `nodes.yaml` file. Defaults to `nodes.yaml`.

**Example:**
```bash
dockyman status
```

### Setup Command

The `setup` command is used to check, install or uninstall the required software in your nodes.

```bash
dockyman setup [action] [nodes_file]
```

- **action**: Required. The action can be `check`, `install` or `uninstall`.
- **nodes_file**: Optional. The path to the `nodes.yaml` file. Defaults to `nodes.yaml`.

**Example:**
```bash
dockyman setup check
```

### Build Command

The `build` command is used to build the base and the local images in your nodes.

```bash
dockyman build [target] [nodes_file]
```

- **target**: Optional. The target can be `base`, `local` or `both` (default).
- **nodes_file**: Optional. The path to the `nodes.yaml` file. Defaults to `nodes.yaml`.

**Example:**
```plaintext
dockyman build local
```

### Pull Command

The `pull` command is used to pull Docker base images specified in the configuration files.

```bash
dockyman pull [nodes_file] [registry]
```

- **nodes_file**: Optional. The path to the `nodes.yaml` file. Defaults to `nodes.yaml`.
- **registry**: Optional. The Docker registry to pull images from. Defaults to an empty string, meaning the images will be pulled without specifying a registry.

**Example:**
```bash
dockyman pull
```

### Push Command

The `push` command is used to push Docker base images specified in the configuration files to a Docker registry.

```bash
dockyman push [nodes_file] [registry]
```

- **nodes_file**: Optional. The path to the `nodes.yaml` file. Defaults to `nodes.yaml`.
- **registry**: Optional. The Docker registry to push images to. Defaults to an empty string, meaning the images will be pushed to the default registry.

**Example:**
```bash
dockyman push
```

### Run Command

The `run` command is used to deploy the local images in your nodes.

```bash
dockyman run
```

### Stop Command

The `stop` command is used to stop the containers of the local images in your nodes.

```bash
dockyman stop
```

## Best Practices

### Security Considerations

- **SSH Key Management**: Ensure that SSH keys are securely managed and only authorized users can access the nodes.
- **Environment Variables**: Avoid hardcoding sensitive data in the `dockyman.env` file. Use Docker secrets or environment variable files that are not committed to version control.
- **User Permissions**: Always validate that the Docker containers are running with the correct user permissions, especially when dealing with graphical and audio applications.

### Managing Node Configurations

- **Static vs. Dynamic Configurations**: While the current setup is static, consider implementing scripts to automate node discovery and configuration updates if your environment is dynamic.
- **Testing Node Connectivity**: Regularly test SSH and Docker daemon connectivity between nodes to ensure that the swarm operates smoothly.

### Logging and Error Handling

- **Centralized Logging**: Implement a centralized logging solution to collect logs from all nodes, which will help in debugging and monitoring.
- **Error Notifications**: Set up alerts or notifications for critical errors during Docker operations, such as failed builds or deployments.

## Support

If you encounter issues or need further assistance, please refer to the [Dockyman GitHub repository](https://github.com/s4hri/dockyman) for documentation, or contact the project maintainers.