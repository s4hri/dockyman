#!/bin/bash

DOCKER_COMPOSE_FILE="compose.yaml"
SERVICE_NAME="dockyman"

DOCKYMAN_VER=$(grep -o 'DOCKYMAN_VER=[^ ]*' .env | cut -d= -f2)
sed -i "s/^DOCKYMAN_VER=.*/DOCKYMAN_VER=$DOCKYMAN_VER/" ./template/build.env

docker-compose -f "$DOCKER_COMPOSE_FILE" build "$SERVICE_NAME"