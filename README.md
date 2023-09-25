DOCKYMAN
========

DOCKYMAN is a toolbox for GNU/Linux OS to manage Docker containers using local resources.
It provides useful tools and templates to develop with Dockers in different use cases.


Use cases
=========

I want to create a Docker project for running:

1. graphical applications using the X11 server running in the host machine (NVIDIA GPUs supported).

2. audio applications using PulseAudio server running in the host machine. 

3. custom bash scripts in the host machine before the container has started.

4. custom bash scripts in the container right after its execution.

5. custom bash script logging hardware/software specifications of the host machine.

6. a container with a non-root user having the same UIDs/GIDs of the current logged user in the host machine.

7. a container with non-root user with with specific group permissions (sudo, audio, video, ...) with the same gids of the host machine.


Minimum requirements
====================

- GNU/Linux OS (Ubuntu, Debian, CentOS, Alpine)
- Basic packages: make, sudo, curl, wget
- Docker CE and docker-compose (optional)
- Visual Studio Code (optional)


Get Started
===========

1. VS CODE

A simple way to start working with Dockyman is to start with a template example and customize it as you prefer inside the VS Code IDE. The following steps will allow you to download the files necessary to start. Once correctly initialized, you can start customizing the template and use VS Code IDE and then
press F1 -> "Dev Container Rebuild and Reopen in Container"

::

    $ cd <myrepo>
    
    $ docker run -it -v ${PWD}:/shared iitschri/dockyman --action init --own $(id -u):$(id -g)

    $ code .


2. BASH

::

    $ cd <myrepo>
    
    $ docker run -it -v ${PWD}:/shared iitschri/dockyman --action init --own $(id -u):$(id -g)

    $ cd .dockyman

    $ make run


How it works
============

Dockyman allows developers to take advantage from its predefined templates and tools for building and running Docker containers, with a focus on those containers that use local resources of the host machine. Dockyman provides a simplified way for building and running Docker images based on a predefined structure of compose files. In one hand, the building is a two-stage process where a 'LOCAL' Docker image is built on top of a 'BASE' Docker image. While the 'BASE' image represents any Docker image that can be pulled or built from a Dockerfile, the 'LOCAL' image is the additional layer built on top of the 'BASE' image for configuring the container to run accordingly with the user specifications. On the other hand, the running process simplify the work of the user by dealing with run arguments and cleaning processes.

Troubleshooting
===============

Learn how to solve common issue that you may encounter using DOCKYMAN

## 1. Cache issues

### 1.1 It seems like the Docker containers are not actually updated based on their related Dockerfiles and build arguments.

In order to remove Docker images built with DOCKYMAN and defined in the compose files `compose.base.yaml` and `compose.local.yaml`) you can rebuild with a complete cleaning of the cache with the following command. Please notice that this procedure will also remove the volumes defined in the main compose file `compose.yaml`.

::

    cd .dockyman
    make rebuild




License
=======

This software is licensed under the `MIT License`. See the ``LICENSE``
file in the top distribution directory for the full license text.
