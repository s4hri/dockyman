#!/bin/bash
set -e

# Load environment variables
set -a
. ./build.env
set +a

DOCKYMAN_YAML="../dockyman/model/dockyman.yaml"
INSTALLER_SH="../dockyman/model/.dockyman_installer/dockyman.sh"
README_SRC="../README.md"
README_DEST="../dockyman/model/README.md"

# Update version in dockyman.yaml (must match indentation and key exactly)
sed -i "s/^  dockyman_version: .*/  dockyman_version: $DOCKYMAN_VER/" "$DOCKYMAN_YAML"

# Update installer script version
sed -i "s/^DOCKYMAN_VER=.*/DOCKYMAN_VER=$DOCKYMAN_VER/" "$INSTALLER_SH"

# Copy README
cp "$README_SRC" "$README_DEST"

# Build Docker image
docker build -t "$DOCKYMAN_IMAGE_NAME:$DOCKYMAN_VER" \
    --build-arg DOCKYMAN_VER="$DOCKYMAN_VER" \
    -f Dockerfile ..
