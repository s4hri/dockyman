#!/bin/bash

# Determine the correct Docker Compose command
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKERCOMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKERCOMPOSE_CMD="docker-compose"
else
    echo "Neither docker compose nor docker-compose is installed. Please install one of them."
    exit 1
fi

# Get the Docker image tag based on DOCKYMAN_VER in the environment
get_docker_image_tag() {
    # Source the dockyman.env file within the function
    if [ -f "$(pwd)/dockyman.env" ]; then
        source "$(pwd)/dockyman.env"
    fi

    # Check if DOCKYMAN_VER is set
    if [[ -n "$DOCKYMAN_VER" ]]; then
        echo "$DOCKYMAN_VER"
    else
        echo "latest"
    fi
}

# Run the dockyman command inside a Docker container
run_dockyman_command() {
    local docker_image_tag=$1
    shift
    
    # Check if the script is running in an interactive shell
    if [ -t 0 ] && [ -t 1 ]; then
        local interactive_flags="-it"
    else
        local interactive_flags=""
    fi
    
    docker run \
           --rm \
           -e LOCALHOST_USER=$(id -nu) \
           -e LOCAL_UID=$(id -u) \
           -e LOCAL_GID=$(id -g) \
           -e PREFIX_TARGET=${PWD} \
           -e SSH_AUTH_SOCK=/run/user/$(id -u)/keyring/ssh \
           -e DOCKER_BUILDKIT=1 \
           -e COMPOSE_DOCKER_CLI_BUILD=1 \
           -e DOCKER_GID=$(getent group docker | cut -d: -f3) \
           -v ${HOME}/.docker:/home/docky/.docker \
           -v ${HOME}/.ssh:/home/docky/.ssh \
           -v ${PWD}:${PWD} \
           -v /run/user/$(id -u)/keyring/ssh:/run/user/$(id -u)/keyring/ssh \
           -v /var/run/docker.sock:/var/run/docker.sock \
           --network host \
           --privileged \
           $interactive_flags "iitschri/dockyman:${docker_image_tag}" "$@"
}


# Main function
main() {
    local docker_image_tag=$(get_docker_image_tag)
    run_dockyman_command "$docker_image_tag" "$@"
}

# Run the main function with all arguments passed to the script
main "$@"
