DOCKYMAN
========

DOCKYMAN is a toolbox for GNU/Linux OS to manage Docker containers using local resources.
It provides useful tools and templates to develop with Dockers in different use cases.


## 1. Use cases

I want to create a Docker project for running:

* Graphical applications using the X11 server running in the host machine (NVIDIA GPUs supported).
* Audio applications using PulseAudio server running in the host machine. 
* Custom bash scripts in the host machine before the container has started.
* Custom bash scripts in the container right after its execution.
* Custom bash script logging hardware/software specifications of the host machine.
* A container with a non-root user having the same UIDs/GIDs of the current logged user in the host machine.
* A container with non-root user with with specific group permissions (sudo, audio, video, ...) with the same GIDs of the host machine.


## 2. Minimum requirements

* GNU/Linux OS (Ubuntu, Debian, CentOS, Alpine)
* Basic packages: git, make, sudo, curl, wget
* Docker CE and docker-compose (if not present, they will be installed automatically by DOCKYMAN)
* Visual Studio Code (optional)


## 3. Get Started

### 3.1 Use the template for your GitHub projects

The easiest way to start using DOCKYMAN is creating a GitHub project from the template.

1. Visit the GitHub repository of the [DOCKYMAN template](https://github.com/s4hri/dockyman-template)

2. Click on the "Use this template" button at the top of the repository.

3. Provide a name for your new repository and choose whether to include all branches, tags, and commit history. Then, click on the "Create repository from template" button.


### 3.2 Use the template in your local machine

### 3.2.1 First download

```bash
cd myrepo
    
docker run -it -v ${PWD}:/shared iitschri/dockyman --action init --own $(id -u):$(id -g)
```

### 3.2.2 Update the template

```bash
cd myrepo
    
docker run -it -v ${PWD}:/shared iitschri/dockyman --action update --own $(id -u):$(id -g)
```

### 3.2.3 Use VSCode

A simple way to start working with DOCKYMAN is to start from a template example and customize it. Once you have correclty initialized the template (for exmple in `myrepo`), you can start customizing it using VS Code IDE. In order to run the container Press F1 -> "Dev Container Rebuild and Reopen in Container".

```bash
cd myrepo

code .
```

## 4. How it works

DOCKYMAN allows developers to take advantage from its predefined templates and tools for building and running Docker containers, with a focus on containers using local resources/devices of the host machine. DOCKYMAN provides a simplified way for building and running Docker images based on a predefined structure of compose files.

## 4.1 The building process

The building is a two-stage process where a `LOCAL` Docker image is built on top of a `BASE` Docker image. 

The `BASE` image(s) is(are) built based on the content of the compose file `compose.base.yaml`. In fact, for each service defined in this compose file, a Docker image is automatically built using devcontainer CLI from the `.devcontainer.json` stored in the folder defined in `--workspace_folder` with image name defined in `--image_name`.

The `LOCAL` image(s) is(are) built based on the content of the compose file `compose.local.yaml`. For each service, defined in this compose file, a Docker image is automatically built adding some predefined packages and the suffix `.local` will be added to the name of the corresponding base image, provided by `--image_name`. Moreover, a user will be created with the name provided in `--username`. Additionally, to the user will be assigned groups provided in `--groups`. For groups, the local container will use the host machine GUIDs corresponding to the selected groups.

To start the entire building process:

```bash
cd .dockyman
make build
```
Eventually, use `make build-base` if you want to build only the base images or `make build-local` for building only the local ones.

## 4.2 Run the container
Once built the base and local image(s) you want to run one or multiple of them. Based on the content of the compose file `compose.yaml` you can actually doing so by running the commands:

```bash
cd myrepo
    
bash go
```

### 4.1 Profiles: Development and Production

DOCKYMAN allows you to distinguish between development and production stages in the building process.

### 4.1.2 Development Profile

In the Develpment profile the building process, for both BASE and LOCAL containers, will be included 

```bash
cd .dockyman
make dev
```

### 4.1.2 Development Profile

```bash
cd .dockyman
make production
```

## 5. Troubleshooting

In the following you can find how to solve common issues you may encounter using DOCKYMAN.

## 5.1 Cache issues

### 5.1.1 It seems like the Docker containers are not actually updated based on their related Dockerfiles and build arguments.

In order to remove Docker images built with DOCKYMAN and defined in the compose files `compose.base.yaml` and `compose.local.yaml`) you can rebuild with a complete cleaning of the cache with the following command. Please notice that this procedure will also remove the volumes defined in the main compose file `compose.yaml`.

```bash
cd .dockyman
make rebuild
```

## 6. Contributing

Pull requests are welcome! We appreciate contributions from the community. Before you start, please take a moment to review the following guidelines:

1. **Open an Issue:**
   - For major changes or new features, it's recommended to open an issue first to discuss the proposed changes. This allows for a broader discussion and ensures that everyone is on the same page.

2. **Fork the Repository:**
   - Fork the repository to your GitHub account and create a new branch for your feature or bug fix.

3. **Tests:**
   - If you're adding new functionality, consider adding relevant tests to ensure the stability of the project. If you're fixing a bug, please make sure to include tests that cover the issue.

5. **Documentation:**
   - Update the documentation to reflect any changes or additions. Clear and concise documentation helps others understand how to use and contribute to the project.

Remember, by contributing to this project, you agree that your contributions will be licensed under the project's license.

Thank you for your interest and support in making this project better!


## 7. License

This software is licensed under the `MIT License`. See the ``LICENSE``
file in the top distribution directory for the full license text.
