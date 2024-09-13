set -a ; . ./build.env ; set +a

docker run --rm \
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
           -it --entrypoint /bin/bash $DOCKYMAN_IMAGE_NAME:$DOCKYMAN_VER

