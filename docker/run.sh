set -a ; . ./build.env ; set +a

docker run --rm \
           -e LOCAL_USERNAME=$(id -nu) \
           -e LOCAL_UID=$(id -u) \
           -e LOCAL_GID=$(id -g) \
           -e PREFIX_TARGET="/shared" \
           -v ${PWD}:/shared \
           -v ~/.ssh:/root/.ssh \
           -v /var/run/docker.sock:/var/run/docker.sock \
           --network host \
           -it --entrypoint /bin/bash $DOCKYMAN_IMAGE_NAME:$DOCKYMAN_VER
