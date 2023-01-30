# MIT License
#
# Copyright (c) 2023 Social Cognition in Human-Robot Interaction
#                    Author: Davide De Tommaso (davide.detommaso@iit.it)
#                    Project: Dockyman
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

ARG VARIANT=20.04
FROM ubuntu:${VARIANT}

ARG USERNAME=docky
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV TZ=Europe/Rome
ENV DEBIAN_FRONTEND noninteractive


RUN apt-get update && apt-get install -y apt-utils nano build-essential cmake git \
                       dialog bash-completion sudo bsdmainutils tzdata \
                       iproute2 procps lsb-release figlet bash curl;

RUN useradd -ms /bin/bash ${USERNAME} && passwd -d ${USERNAME} && usermod -u ${USER_UID} ${USERNAME} && groupmod -g ${USER_GID} ${USERNAME};
RUN echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME  && chmod 0440 /etc/sudoers.d/$USERNAME

ARG NODE_VERSION=v14.21.2

RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update
RUN apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

RUN usermod -aG docker $USERNAME

RUN mkdir -p /shared
VOLUME /shared

USER $USERNAME

RUN mkdir -p ~/nvm
ENV NVM_DIR /home/$USERNAME/nvm

#SHELL ["/bin/bash", "--login", "-c"]

RUN curl -o- curl https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash

RUN /bin/bash -c "source $NVM_DIR/nvm.sh && nvm install $NODE_VERSION && nvm use --delete-prefix $NODE_VERSION"

ENV NODE_PATH $NVM_DIR/versions/node/$NODE_VERSION/bin
ENV PATH $NODE_PATH:$PATH

RUN npm install -g @devcontainers/cli

ADD local /workdir/local
ADD dockyman /workdir/dockyman

COPY dockyman /usr/local/bin

WORKDIR /workdir
ARG DOCKYMAN_VER

ENV DOCKYMAN_VER $DOCKYMAN_VER
