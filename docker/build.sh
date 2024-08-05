#!/bin/bash

DOCKER_COMPOSE_FILE="compose.yaml"
SERVICE_NAME="dockyman"

DOCKYMAN_VER=$(grep -o 'DOCKYMAN_VER=[^ ]*' ../.env | cut -d= -f2)
sed -i "s/^DOCKYMAN_VER=.*/DOCKYMAN_VER=$DOCKYMAN_VER/" ./model/build.env

docker build -t iitschri/dockyman:${DOCKYMAN_VER} .
docker tag iitschri/dockyman:${DOCKYMAN_VER} iitschri/dockyman:latest