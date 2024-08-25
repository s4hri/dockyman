set -a ; . ./build.env ; set +a

docker run --rm \
           -e LOCALHOST_USER="$user" \
           -e LOCAL_USERNAME=$(id -nu) \
           -e LOCAL_UID=$(id -u) \
           -e LOCAL_GID=$(id -g) \
           -e PREFIX_TARGET="/shared" \
           -e SSH_AUTH_SOCK=/run/user/$(id -u)/keyring/ssh \
           -e DOCKER_BUILDKIT=1 \
           -e COMPOSE_DOCKER_CLI_BUILD=1 \
           -e DOCKER_GID=$(getent group docker | cut -d: -f3) \
           -v "${HOME}/.ssh:/home/docky/.ssh" \
           -v "$(pwd):/shared" \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v $SSH_AUTH_SOCK:/run/user/$(id -u)/keyring/ssh \
           --network host \
           --privileged \
           -it --entrypoint /bin/bash $DOCKYMAN_IMAGE_NAME:$DOCKYMAN_VER

