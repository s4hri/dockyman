# MIT License
#
# Copyright (c) 2025 Istituto Italiano di Tecnoogia
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

ARG DOCKER_SRC=ubuntu:latest
FROM ${DOCKER_SRC}

LABEL maintainer="Davide De Tommaso <davide.detommaso@iit.it>"
LABEL version="local"

ENV DEBIAN_FRONTEND=noninteractive

USER root
WORKDIR /workdir

# Install basic tools depending on distro
RUN if [ -f /etc/alpine-release ]; then \
        apk update && apk add sudo bash shadow; \
    elif [ -f /etc/debian_version ]; then \
        apt-get update && apt-get install -y sudo bash; \
    elif [ -f /etc/redhat-release ]; then \
        yum update -y && yum install -y sudo bash shadow; \
    elif [ -f /etc/arch-release ]; then \
        pacman -Syy && pacman -S --noconfirm sudo bash shadow; \
    else \
        echo "Unsupported distribution" && exit 1; \
    fi

# Args and ENV
ARG USERNAME
ARG USER_UID
ARG USER_GID
ARG USER_GROUPS      # ex: "sudo,audio,video,input,dialout"
ARG GROUP_IDS        # ex: "27,29,44,104,20"

ENV USERNAME=$USERNAME
ENV USER_UID=$USER_UID
ENV USER_GID=$USER_GID
ENV USER_GROUPS=$USER_GROUPS
ENV GROUP_IDS=$GROUP_IDS

SHELL ["/bin/bash", "-c"]

# Crea o rinomina i gruppi, mappando USER_GROUPS con GROUP_IDS
RUN IFS=',' read -ra group_names <<< "$USER_GROUPS"; \
    IFS=',' read -ra group_ids <<< "$GROUP_IDS"; \
    for i in "${!group_names[@]}"; do \
        gname="${group_names[$i]}"; \
        gid="${group_ids[$i]}"; \
        existing_group=$(getent group "$gid" | cut -d: -f1); \
        if [ -n "$existing_group" ] && [ "$existing_group" != "$gname" ]; then \
            echo "Renaming group $existing_group (GID=$gid) to $gname"; \
            groupmod -n "$gname" "$existing_group"; \
        elif ! getent group "$gname" >/dev/null; then \
            echo "Creating group $gname with GID=$gid"; \
            groupadd -g "$gid" "$gname"; \
        fi; \
    done

# Gestione gruppo principale (GID)
RUN existing_group=$(getent group "$USER_GID" | cut -d: -f1); \
    if [ -n "$existing_group" ] && [ "$existing_group" != "$USERNAME" ]; then \
        echo "Renaming group $existing_group (GID=$USER_GID) to $USERNAME"; \
        groupmod -n "$USERNAME" "$existing_group"; \
    elif ! getent group "$USERNAME" >/dev/null; then \
        groupadd -g "$USER_GID" "$USERNAME"; \
    fi

# Gestione utente
RUN existing_user=$(getent passwd "$USER_UID" | cut -d: -f1); \
    if [ -n "$existing_user" ] && [ "$existing_user" != "$USERNAME" ]; then \
        echo "Renaming user $existing_user (UID=$USER_UID) to $USERNAME"; \
        usermod -l "$USERNAME" "$existing_user"; \
        usermod -d "/home/$USERNAME" -m "$USERNAME"; \
        usermod -u "$USER_UID" "$USERNAME"; \
        usermod -g "$USER_GID" "$USERNAME"; \
    elif ! id "$USERNAME" >/dev/null 2>&1; then \
        echo "Creating user $USERNAME"; \
        useradd --no-log-init -m -d "/home/$USERNAME" -u "$USER_UID" -g "$USER_GID" -s /bin/bash "$USERNAME"; \
    fi && \
    passwd -d "$USERNAME"

# Aggiunge l'utente ai gruppi secondari
RUN IFS=',' read -ra group_names <<< "$USER_GROUPS"; \
    for g in "${group_names[@]}"; do \
        usermod -aG "$g" "$USERNAME"; \
    done

# Sudo senza password se serve
RUN if echo "$USER_GROUPS" | grep -qw "sudo"; then \
        echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$USERNAME"; \
        chmod 0440 "/etc/sudoers.d/$USERNAME"; \
    fi

# Cleanup
RUN rm -f /var/log/lastlog /var/log/faillog /var/log/dpkg.log

# PATH update
ENV PATH=${PATH}:/home/${USERNAME}/.local/bin:/workdir

RUN touch /.Xauthority && chmod 600 /.Xauthority

USER $USERNAME

