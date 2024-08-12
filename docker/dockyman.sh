#!/bin/bash

# Determine the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from dockyman.env file located in the script's directory
load_dockyman_env() {
    if [[ -f "${SCRIPT_DIR}/dockyman.env" ]]; then
        while IFS= read -r line; do
            # Skip lines that are comments or don't contain an equal sign
            if [[ "$line" =~ ^[^#]*= ]]; then
                export "$line"
            fi
        done < "${SCRIPT_DIR}/dockyman.env"
    fi
}

# Get the Docker image tag based on DOCKYMAN_VER in the environment
get_docker_image_tag() {
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
    local user=$(id -un)
    local uid=$(id -u)
    local gid=$(id -g)
    
    docker run \
        --rm \
        -e LOCALHOST_USER="$user" \
        -e LOCAL_UID="$uid" \
        -e LOCAL_GID="$gid" \
        -e PREFIX_TARGET="/shared" \
        -v "${HOME}/.ssh:/root/.ssh" \
        -v "$(pwd):/shared" \
        -v /var/run/docker.sock:/var/run/docker.sock \
        --network host \
        --privileged \
        -it "iitschri/dockyman:${docker_image_tag}" "$@"
}

# Run docker compose commands for each node.id in nodes.yaml
run_docker_compose_for_nodes() {
    if [[ -f "nodes.yaml" ]]; then
        local current_dir=$(pwd)
        
        # Parse nodes.yaml to get node IDs and their corresponding docker_daemon_address
        local nodes=$(grep -oP 'id:\s*\K\S+|docker_daemon_address:\s*\K\S+' nodes.yaml | paste - -)
        
        while IFS=$'\t' read -r node_id docker_daemon_address; do
            echo "Running docker compose -f ${current_dir}/compose.yaml --profile $node_id --host $docker_daemon_address up -d"
            DOCKER_HOST="$docker_daemon_address" docker compose -f "${current_dir}/compose.yaml" --profile "$node_id" up -d
        done <<< "$nodes"
        
    else
        echo "nodes.yaml file not found!"
        exit 1
    fi
}

# Main function
main() {
    load_dockyman_env
    if [[ "$1" == "run" ]]; then
        shift
        run_docker_compose_for_nodes "$@"
    else
        local docker_image_tag=$(get_docker_image_tag)
        run_dockyman_command "$docker_image_tag" "$@"
    fi
}

# Run the main function with all arguments passed to the script
main "$@"
