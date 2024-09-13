#!/bin/bash
set -e

# Dynamically update docky user's UID and GID
if [ -n "$LOCAL_UID" ] && [ -n "$LOCAL_GID" ]; then
    usermod -u $LOCAL_UID docky 2>&1 | grep -v "usermod: no changes" || true
    groupmod -g $LOCAL_GID docky 2>&1 | grep -v "groupmod: no changes" || true
    chown -R docky:docky /home/docky 2>/dev/null
fi

# Check if DOCKER_GID is set and modify docker group GID accordingly
if [ -n "$DOCKER_GID" ]; then
    current_gid=$(getent group docker | cut -d: -f3)
    if [ "$current_gid" != "$DOCKER_GID" ]; then
        groupmod -g $DOCKER_GID docker 2>&1 | grep -v "groupmod: no changes" || true
    fi
fi

exec gosu docky python /app/dockyman/cli.py "$@"
