# MIT License
#
# Copyright (c) 2025 Istituto Italiano di Tecnoogia
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


ARG DOCKER_SRC=ubuntu:latest
FROM ${DOCKER_SRC}

LABEL maintainer="Davide De Tommaso <davide.detommaso@iit.it>"
LABEL version="local"

ENV DEBIAN_FRONTEND=noninteractive

USER root
WORKDIR /workdir

# Install system utilities if needed
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

# Build arguments
ARG USERNAME
ARG USER_UID
ARG USER_GID
ARG USER_GROUPS
ARG GROUP_IDS
ARG XDG_RUNTIME_DIR


ENV USERNAME=$USERNAME
ENV USER_UID=$USER_UID
ENV USER_GID=$USER_GID
ENV USER_GROUPS=$USER_GROUPS
ENV GROUP_IDS=$GROUP_IDS
ENV XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR

SHELL ["/bin/bash", "-c"]

# Create workdir if it doesn't exist
RUN mkdir -p /workdir

# Step 1: Ensure all secondary groups exist (with specified GIDs)
RUN IFS=',' read -ra group_names <<< "$USER_GROUPS"; \
    IFS=',' read -ra group_ids <<< "$GROUP_IDS"; \
    for i in "${!group_names[@]}"; do \
        g="${group_names[$i]}"; \
        gid="${group_ids[$i]}"; \
        existing=$(getent group "$gid" | cut -d: -f1); \
        if [ -n "$existing" ] && [ "$existing" != "$g" ]; then \
            echo "Renaming group $existing to $g"; \
            groupmod -n "$g" "$existing"; \
        elif ! getent group "$g" >/dev/null; then \
            echo "Creating group $g with GID $gid"; \
            groupadd -g "$gid" "$g"; \
        fi; \
    done

# Step 2: Ensure main group (USERNAME) exists and has correct GID
RUN existing_group_info=$(getent group "$USERNAME"); \
    user_exists=$(id -u "$USERNAME" 2>/dev/null || true); \
    \
    if [ -n "$existing_group_info" ]; then \
        existing_gid=$(echo "$existing_group_info" | cut -d: -f3); \
        if [ "$existing_gid" != "$USER_GID" ]; then \
            echo "Group '$USERNAME' exists with wrong GID ($existing_gid), fixing..."; \
            if [ -n "$user_exists" ]; then \
                echo "Temporarily changing '$USERNAME' user to group 'root'"; \
                usermod -g root "$USERNAME"; \
            fi; \
            echo "Deleting group '$USERNAME'..."; \
            groupdel "$USERNAME"; \
            echo "Recreating group '$USERNAME' with GID=$USER_GID"; \
            groupadd -g "$USER_GID" "$USERNAME"; \
            if [ -n "$user_exists" ]; then \
                echo "Assigning '$USERNAME' back to group '$USERNAME' (GID=$USER_GID)"; \
                usermod -g "$USER_GID" "$USERNAME"; \
            fi; \
        else \
            echo "Group '$USERNAME' exists with correct GID=$USER_GID"; \
        fi; \
    elif getent group "$USER_GID" >/dev/null; then \
        existing_group=$(getent group "$USER_GID" | cut -d: -f1); \
        echo "GID $USER_GID is used by group '$existing_group'. Renaming it to '$USERNAME'"; \
        groupmod -n "$USERNAME" "$existing_group"; \
    else \
        echo "Creating group '$USERNAME' with GID=$USER_GID"; \
        groupadd -g "$USER_GID" "$USERNAME"; \
    fi


# Step 3: Modify the existing user (from UID 1000) to match local UID/GID
RUN existing_user_by_uid=$(getent passwd "$USER_UID" | cut -d: -f1 || true); \
    if id "$USERNAME" >/dev/null 2>&1; then \
        echo "User '$USERNAME' already exists."; \
        current_uid=$(id -u "$USERNAME"); \
        current_gid=$(id -g "$USERNAME"); \
        if [ "$current_uid" != "$USER_UID" ]; then \
            echo "Updating UID of '$USERNAME' from $current_uid to $USER_UID"; \
            usermod -u "$USER_UID" "$USERNAME"; \
        fi; \
        if [ "$current_gid" != "$USER_GID" ]; then \
            echo "Updating GID of '$USERNAME' from $current_gid to $USER_GID"; \
            usermod -g "$USER_GID" "$USERNAME"; \
        fi; \
        usermod -d "/home/$USERNAME" -m -s /bin/bash "$USERNAME"; \
        passwd -d "$USERNAME"; \
    elif [ -n "$existing_user_by_uid" ]; then \
        echo "Found existing user with UID=$USER_UID: '$existing_user_by_uid'"; \
        usermod -l "$USERNAME" "$existing_user_by_uid"; \
        usermod -d "/home/$USERNAME" -m -s /bin/bash "$USERNAME"; \
        groupmod -n "$USERNAME" "$existing_user_by_uid"; \
        passwd -d "$USERNAME"; \
    else \
        echo "Creating new user '$USERNAME' with UID=$USER_UID and GID=$USER_GID"; \
        useradd --no-log-init -m -d "/home/$USERNAME" -u "$USER_UID" -g "$USER_GID" -s /bin/bash "$USERNAME"; \
        passwd -d "$USERNAME"; \
    fi


# Step 4: Add the user to the specified groups
RUN IFS=',' read -ra group_names <<< "$USER_GROUPS"; \
    for g in "${group_names[@]}"; do \
        usermod -aG "$g" "$USERNAME"; \
    done

# Step 5: Grant passwordless sudo if applicable
RUN if echo "$USER_GROUPS" | grep -qw "sudo"; then \
        echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$USERNAME"; \
        chmod 0440 "/etc/sudoers.d/$USERNAME"; \
    fi

# Step 6: Clean logs
RUN rm -f /var/log/lastlog /var/log/faillog /var/log/dpkg.log

# Step 7: Fix ownership of home directory and workdir
RUN chown -R "$USER_UID:$USER_GID" "/home/$USERNAME" && \
    chown -R "$USER_UID:$USER_GID" "/workdir"

# Step 8: Ensure the XDG_RUNTIME_DIR directory has the correct permissions
RUN if [ -n "$XDG_RUNTIME_DIR" ]; then \
        mkdir -p "$XDG_RUNTIME_DIR"; \
        chmod 0700 "$XDG_RUNTIME_DIR"; \
        chown "$USER_UID:$USER_GID" "$XDG_RUNTIME_DIR"; \
    else \
        echo "XDG_RUNTIME_DIR is not set, skipping"; \
    fi

# Step 9: Optional X11 support
RUN touch /.Xauthority && chmod 600 /.Xauthority

# Step 10: Set environment and switch to user
ENV PATH=${PATH}:/home/${USERNAME}/.local/bin:/workdir
USER $USERNAME

RUN pip install markdown