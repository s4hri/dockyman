DOCKYMAN
========

Dockyman is a toolbox for GNU/Linux OS to manage Docker containers using local resources.
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

A simple way to start working with Dockyman is to start with a template example and customize it as you prefer inside the VS Code IDE. The following steps will allow you to download the files necessary to start.

::
    $ cd <myrepo>
    
    $ docker run -it --network=host iitschri/dockyman --action init --target ${PWD} --username ${USER} --hostname ${HOSTNAME}

    $ code .


How it works
============

Dockyman allows developers to take advantage from its predefined templates and tools for building and running Docker containers, with a focus on those containers that use local resources of the host machine. Dockyman provides a simplified way for building and running Docker images based on a predefined structure of compose files. In one hand, the building is a two-stage process where a 'LOCAL' Docker image is built on top of a 'BASE' Docker image. While the 'BASE' image represents any Docker image that can be pulled or built from a Dockerfile, the 'LOCAL' image is the additional layer built on top of the 'BASE' image for configuring the container to run accordingly with the user specifications. On the other hand, the running process simplify the work of the user by dealing with run arguments and cleaning processes.


License
=======

This software is licensed under the `MIT License`. See the ``LICENSE``
file in the top distribution directory for the full license text.
