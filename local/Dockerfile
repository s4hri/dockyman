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

# Use bash as the shell for RUN commands
SHELL ["/bin/bash", "-c"]

# Step 1: Read and split the user groups and IDs into arrays
RUN read -ra groups_array <<< "$USER_GROUPS" && \
    read -ra ids_array <<< "$GROUP_IDS"

# Step 2: Loop through the arrays to create or modify groups
RUN for i in "${!groups_array[@]}"; do \
        printf "%s\t%s\t%s\n" "$i" "${groups_array[$i]}" "${ids_array[$i]}"; \
        if getent group "${groups_array[$i]}" >/dev/null; then \
            groupmod -o "${groups_array[$i]}" --gid "${ids_array[$i]}"; \
        else \
            groupadd "${groups_array[$i]}" --gid "${ids_array[$i]}"; \
        fi; \
    done

# Step 3: Check and create/modify the user
RUN if ! getent passwd "$USER_UID" >/dev/null; then \
        if getent passwd "$USERNAME" >/dev/null; then \
            echo "User exists"; \
            usermod -u "$USER_UID" "$USERNAME"; \
            groupmod -g "$USER_GID" "$USERNAME"; \
            passwd -d "$USERNAME"; \
        else \
            echo "User not found"; \
            useradd --no-log-init -m -d "/home/$USERNAME" "$USERNAME"; \
            passwd -d "$USERNAME"; \
            usermod -u "$USER_UID" "$USERNAME"; \
            groupmod -g "$USER_GID" "$USERNAME"; \
        fi; \
    else \
        echo "UID exists"; \
        old_uname=$(getent passwd "$USER_UID" | cut -d: -f1); \
        usermod -l "$USERNAME" "$old_uname"; \
        groupmod -n "$USERNAME" "$old_uname"; \
    fi

# Step 4: Set user shell and home directory ownership
RUN usermod -ms /bin/bash -d "/home/$USERNAME" "$USERNAME" && \
    chown -R "$USER_UID:$USER_GID" "/home/$USERNAME"

# Step 5: Check if "sudo" group is in the list and modify sudoers if necessary
RUN if [[ " ${groups_array[*]} " =~ " sudo " ]]; then \
        echo "$USERNAME ALL=(root) NOPASSWD:ALL" > "/etc/sudoers.d/$USERNAME"; \
        chmod 0440 "/etc/sudoers.d/$USERNAME"; \
        usermod -a -G root "$(getent passwd "$USER_UID" | cut -d: -f1)"; \
    fi

# Step 6: Add the user to additional groups specified by GROUP_IDS
RUN usermod -a -G "$GROUP_IDS" "$(getent passwd "$USER_UID" | cut -d: -f1)"

RUN rm -f /var/log/lastlog /var/log/faillog /var/log/dpkg.log

ENV PATH=${PATH}:/home/${USERNAME}/.local/bin:/workdir

USER $USERNAME