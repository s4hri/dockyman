#!/bin/bash

# Load environment variables from dockyman.env file
load_dockyman_env() {
    if [[ -f "dockyman.env" ]]; then
        while IFS= read -r line; do
            # Skip lines that are comments or don't contain an equal sign
            if [[ "$line" =~ ^[^#]*= ]]; then
                export "$line"
            fi
        done < dockyman.env
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
        -e LOCAL_USERNAME="$user" \
        -e LOCAL_UID="$uid" \
        -e LOCAL_GID="$gid" \
        -e PREFIX_TARGET="/shared" \
        -v "${HOME}/.ssh:/root/.ssh" \
        -v "$(pwd):/shared" \
        -v /var/run/docker.sock:/var/run/docker.sock \
        --network host \
        -it "iitschri/dockyman:${docker_image_tag}" "$@"
}

# Main function
main() {
    load_dockyman_env
    local docker_image_tag=$(get_docker_image_tag)
    run_dockyman_command "$docker_image_tag" "$@"
}

# Run the main function with all arguments passed to the script
main "$@"
