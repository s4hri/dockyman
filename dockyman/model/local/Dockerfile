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

ENV USERNAME=$USERNAME
ENV USER_UID=$USER_UID
ENV USER_GID=$USER_GID
ENV USER_GROUPS=$USER_GROUPS
ENV GROUP_IDS=$GROUP_IDS

SHELL ["/bin/bash", "-c"]

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
RUN if id "$USERNAME" >/dev/null 2>&1; then \
        current_uid=$(id -u "$USERNAME"); \
        current_gid=$(id -g "$USERNAME"); \
        if [ "$current_uid" != "$USER_UID" ]; then \
            echo "Updating UID of user '$USERNAME' from $current_uid to $USER_UID"; \
            usermod -u "$USER_UID" "$USERNAME"; \
        fi; \
        if [ "$current_gid" != "$USER_GID" ]; then \
            echo "Updating GID of user '$USERNAME' from $current_gid to $USER_GID"; \
            usermod -g "$USER_GID" "$USERNAME"; \
        fi; \
        usermod -d "/home/$USERNAME" -m -s /bin/bash "$USERNAME"; \
        passwd -d "$USERNAME"; \
    else \
        echo "User '$USERNAME' not found. Creating..."; \
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

# Step 7: Fix ownership of home directory
RUN echo "Fixing permissions for /home/$USERNAME"; \
    chown -R "$USER_UID:$USER_GID" "/home/$USERNAME"

# Step 8: Optional X11 support
RUN touch /.Xauthority && chmod 600 /.Xauthority

# Step 9: Set environment and switch to user
ENV PATH=${PATH}:/home/${USERNAME}/.local/bin:/workdir
USER $USERNAME