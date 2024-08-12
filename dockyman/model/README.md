
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
5. [Best Practices](#best-practices)
   - [Security Considerations](#security-considerations)
   - [Managing Node Configurations](#managing-node-configurations)
   - [Logging and Error Handling](#logging-and-error-handling)
6. [Support](#support)

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
   sh -c 'curl -O https://s4hri/dockyman/docker/dockyman.sh && chmod +x dockyman.sh && sudo mv dockyman.sh /usr/local/bin/dockyman'
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
   - `profiles:` Indicates which nodes this build should apply to (nodes are defined in `nodes.yaml`).

5. **Configure your Local Docker Images**:
   Update the `local/compose.yaml` services that will build Local Docker Images during the building process.

   **Key Points:**
   - `image:` Defines the base image name.
   - `build:` Customizes the image build to match the user and group configurations of the host.
   - `profiles:` As with the base image, this section specifies which nodes the service applies to.

6. **Configure the Main Compose File**:
   Update the `compose.yaml` services that will run Local Docker Images during the deployment process.

   **Key Points:**
   - `image:` Defines the base image name.
   - `build:` Specifies the context, Dockerfile, and build arguments.
   - `profiles:` Indicates which nodes this build should apply to (nodes are defined in `nodes.yaml`).

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

## Customizing the Configuration

### Customizing `dockyman.env`

The `dockyman.env` file contains global settings that affect your Docker environment:

- **`VERSION`**: The version of your project.
- **`DOCKYMAN_VER`**: The version of the Dockyman tool.
- **`BASE_PROJECT_NAME`**: The base name for your Docker project.
- **`BASE_IMAGE_SRC`**: The base Docker image source (e.g., `alpine:latest`, `ubuntu:latest`).
- **`LOCAL_IMAGE_NAME`**: The name of the local Docker image, derived from the base image.
- **`LOCAL_IMAGE_GROUPS`**: Comma-separated list of user groups (e.g., `sudo,audio,video`) that the local Docker user should belong to.
- **`LOCAL_IMAGE_USERNAME`**: The username for the non-root user within the container.

### Customizing `nodes.yaml`

The `nodes.yaml` file defines your Docker Swarm configuration:

- **Manager Node**:
  - `id`: Identifier for the manager node.
  - `host`: IP address or hostname of the manager node.
  - `user`: SSH user to connect to the manager node (supports environment variables like `${LOCALHOST_USER}`).
  - `ssh_port`: SSH port (default is 22).
  - `docker_daemon_address`: Docker daemon address (e.g., `unix:///var/run/docker.sock`).

- **Worker Nodes**:
  - `id`: Identifier for each worker node.
  - `host`: IP address or hostname of the worker node.
  - `user`: SSH user to connect to the worker node.
  - `ssh_port`: SSH port.
  - `docker_daemon_address`: Docker daemon address (e.g., `ssh://user@host`).

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