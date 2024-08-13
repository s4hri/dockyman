#!/bin/bash

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
        -v "${HOME}/.docker:/root/.docker" \
        -v /var/run/docker.sock:/var/run/docker.sock \
        --network host \
        --privileged \
        -it "iitschri/dockyman:${docker_image_tag}" "$@"
}


# Run docker compose up commands for manager and workers
run_docker_compose_up_for_all() {
    if [[ -f "nodes.yaml" ]]; then
        local current_dir=$(pwd)

        # Extract manager node details
        local manager=$(grep -v '^\s*#' nodes.yaml | grep -v '^\s*$' | awk '/manager:/{flag=1; next} /workers:/{flag=0} flag' | grep -oP 'id:\s*\K\S+|docker_daemon_address:\s*\K\S+' | paste - -)

        # Extract worker nodes details
        local workers=$(grep -v '^\s*#' nodes.yaml | grep -v '^\s*$' | awk '/workers:/{flag=1; next} /manager:/{flag=0} flag' | grep -oP 'id:\s*\K\S+|docker_daemon_address:\s*\K\S+' | paste - -)

        bash "${current_dir}/scripts/initHost.sh"

        # Run docker compose up for the manager node
        if [[ -n "$manager" ]]; then
            IFS=$'\t' read -r manager_id manager_daemon_address <<< "$manager"
            DOCKER_HOST="$manager_daemon_address" docker compose -f "${current_dir}/compose.yaml" --env-file "${current_dir}/.env" --profile "$manager_id" up -d
        fi

        # Check if the workers variable is empty
        if [ -z "$workers" ]; then
            echo "No workers defined, skipping Docker Compose up."
        else
            # Run docker compose up for the worker nodes
            while IFS=$'\t' read -r worker_id worker_daemon_address; do
                DOCKER_HOST="$worker_daemon_address" docker compose -f "${current_dir}/compose.yaml" --env-file "${current_dir}/.env-$worker_id" --profile "$worker_id" up -d
            done <<< "$workers"
        fi        
    else
        echo "nodes.yaml file not found!"
        exit 1
    fi
}

run_docker_compose_down_for_all() {
    if [[ -f "nodes.yaml" ]]; then
        local current_dir=$(pwd)

        # Extract manager node details
        local manager=$(grep -v '^\s*#' nodes.yaml | grep -v '^\s*$' | awk '/manager:/{flag=1; next} /workers:/{flag=0} flag' | grep -oP 'id:\s*\K\S+|docker_daemon_address:\s*\K\S+' | paste - -)

        # Extract worker nodes details
        local workers=$(grep -v '^\s*#' nodes.yaml | grep -v '^\s*$' | awk '/workers:/{flag=1; next} /manager:/{flag=0} flag' | grep -oP 'id:\s*\K\S+|docker_daemon_address:\s*\K\S+' | paste - -)

        # Run docker compose down for the manager node
        if [[ -n "$manager" ]]; then
            IFS=$'\t' read -r manager_id manager_daemon_address <<< "$manager"
            DOCKER_HOST="$manager_daemon_address" docker compose -f "${current_dir}/compose.yaml" --env-file "${current_dir}/.env" --profile "$manager_id" down
        fi

        # Check if the workers variable is empty
        if [ -z "$workers" ]; then
            echo "No workers defined, skipping Docker Compose up."
        else
            # Run docker compose down for the worker nodes
            while IFS=$'\t' read -r worker_id worker_daemon_address; do
                DOCKER_HOST="$worker_daemon_address" docker compose -f "${current_dir}/compose.yaml" --env-file "${current_dir}/.env-$worker_id" --profile "$worker_id" down
            done <<< "$workers"
        fi        
    else
        echo "nodes.yaml file not found!"
        exit 1
    fi
}


# Main function
main() {
    #load_dockyman_env
    if [[ "$1" == "run" ]]; then
        shift
        run_docker_compose_up_for_all "$@"
    elif [[ "$1" == "stop" ]]; then
        shift
        run_docker_compose_down_for_all "$@"
    else
        local docker_image_tag=$(get_docker_image_tag)
        run_dockyman_command "$docker_image_tag" "$@"
    fi
}

# Run the main function with all arguments passed to the script
main "$@"
