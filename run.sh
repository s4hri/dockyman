#!/bin/bash

DOCKER_COMPOSE_FILE="compose.yaml"
SERVICE_NAME="dockyman"

docker compose -f "$DOCKER_COMPOSE_FILE" up

docker compose -f "$DOCKER_COMPOSE_FILE" down
