# MIT License
#
# Copyright (c) 2023 Istituto Italiano di Tecnoogia
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
LABEL version="local"

ENV DEBIAN_FRONTEND noninteractive

USER root

WORKDIR /workdir

RUN if [ -f /etc/alpine-release ]; then \
        apk update; \
        apk add sudo bash shadow; \
    elif [ -f /etc/debian_version ]; then \
        apt-get update; \
        apt-get install -y sudo bash; \
    elif [ -f /etc/redhat-release ]; then \
        yum update; \
        yum install -y sudo bash shadow; \
    elif [ -f /etc/arch-release ]; then \
        pacman -Syy; \
        pacman -S --noconfirm sudo bash shadow; \
    else \
        echo "Unknown distribution"; \
        exit 1; \
    fi

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

# Use bash as the shell for RUN commands
SHELL ["/bin/bash", "-c"]

# Step 2: Loop through the arrays to create or modify groups
RUN IFS=',' read -ra groups_array <<< "$USER_GROUPS" && \
    IFS=',' read -ra ids_array <<< "$GROUP_IDS"; \
    for index in "${!groups_array[@]}"; do \
        group="${groups_array[index]}"; \
        gid="${ids_array[index]}"; \
        printf "Group: %s, GID: %s\n" "$group" "$gid"; \
        if getent group "$group" >/dev/null; then \
            groupmod -o "$group" --gid "$gid"; \
        else \
            groupadd "$group" --gid "$gid"; \
        fi; \
    done

# Step 3: Check if the user exists
RUN if getent passwd "$USERNAME" >/dev/null; then \
        echo "User exists"; \
        usermod -u "$USER_UID" "$USERNAME"; \
        groupmod -g "$USER_GID" "$USERNAME"; \
        passwd -d "$USERNAME"; \
    else \
        # Create/modify the user
        if ! getent passwd "$USER_UID" >/dev/null; then \
            echo "User does not exist"; \
            useradd --no-log-init -m -d "/home/$USERNAME" "$USERNAME"; \
            passwd -d "$USERNAME"; \
            usermod -u "$USER_UID" "$USERNAME"; \
            groupmod -g "$USER_GID" "$USERNAME"; \
        else \
            echo "UID exists"; \
            old_uname=$(getent passwd "$USER_UID" | cut -d: -f1); \
            usermod -l "$USERNAME" "$old_uname"; \
            groupmod -n "$USERNAME" "$old_uname"; \
        fi; \
    fi

# Step 4: Set user shell and home directory ownership
RUN usermod -ms /bin/bash -d "/home/$USERNAME" "$USERNAME" && \
    chown -R "$USER_UID:$USER_GID" "/home/$USERNAME"

# Step 5: Check if "sudo" group is in the list and modify sudoers if necessary
RUN IFS=',' read -ra groups_array <<< "$USER_GROUPS" && \
    if [[ " ${groups_array[*]} " =~ " sudo " ]]; then \
        echo "$USERNAME ALL=(root) NOPASSWD:ALL" > "/etc/sudoers.d/$USERNAME"; \
        chmod 0440 "/etc/sudoers.d/$USERNAME"; \
    fi

# Step 6: Add the user to additional groups specified by GROUP_IDS
RUN IFS=',' read -ra group_names <<< "$GROUP_IDS" && \
    for group_name in "${group_names[@]}"; do \
        if getent group "$group_name" >/dev/null; then \
            usermod -a -G "$group_name" "$(getent passwd "$USER_UID" | cut -d: -f1)"; \
        fi; \
    done

RUN rm -f /var/log/lastlog /var/log/faillog /var/log/dpkg.log

ENV PATH=${PATH}:/home/${USERNAME}/.local/bin:/workdir

RUN touch /.Xauthority && chmod 600 /.Xauthority

USER $USERNAME