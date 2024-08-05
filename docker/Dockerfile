# MIT License
#
# Copyright (c) 2024 Istituto Italiano di Tecnoogia
#                    Author: Davide De Tommaso (davide.detommaso@iit.it)
#                    Project: Dockyman Template
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

FROM node:20.4.0-alpine

ENV TZ=Europe/Rome
ENV DEBIAN_FRONTEND=noninteractive

COPY ./model /workdir/model
COPY ./ansible /workdir/ansible

# Install necessary packages
RUN apk add --no-cache \
    docker \
    docker-compose \
    python3 \
    py3-pip \
    make \
    g++ \
    bash \
    openssh \
    rsync \
    && pip3 install --upgrade pip \
    && pip3 install ansible

# Set the Dockyman version as a build argument
ARG DOCKYMAN_VER

# Set the Dockyman version as an environment variable
ENV DOCKYMAN_VER=$DOCKYMAN_VER

# Install Dev Container CLI
RUN npm install -g @devcontainers/cli

# Set the working directory
WORKDIR /workdir

# Set the default command
CMD ["bash"]
