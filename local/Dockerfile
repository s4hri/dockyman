# MIT License
#
# Copyright (c) 2023 Social Cognition in Human-Robot Interaction
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

ARG DOCKER_SRC

FROM ${DOCKER_SRC}
LABEL maintainer="Davide De Tommaso <davide.detommaso@iit.it>"

ENV DEBIAN_FRONTEND noninteractive

USER root

WORKDIR /workdir

RUN apt-get update && apt-get install -y sudo

ARG USER_UID
ARG USER_GID
ARG USERNAME
ARG USER_GROUPS
ARG GROUP_IDS

ENV USER_UID $USER_UID
ENV USER_GID $USER_GID
ENV USERNAME $USERNAME
ENV USER_GROUPS $USER_GROUPS
ENV GROUP_IDS $GROUP_IDS

COPY configure.sh /root

RUN /bin/bash /root/configure.sh

RUN rm -f /var/log/lastlog /var/log/faillog /var/log/dpkg.log

ENV PATH=${PATH}:/home/${USERNAME}/.local/bin:/workdir

USER $USERNAME