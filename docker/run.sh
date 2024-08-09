set -a ; . ./build.env ; set +a

#docker run -e LOCAL_USERNAME=$(id -nu) -e LOCAL_UID=$(id -u) -e LOCAL_GID=$(id -g) -v ${PWD}:/shared -v ~/.ssh:/root/.ssh --network host -it $DOCKYMAN_IMAGE_NAME:$DOCKYMAN_VER
docker run -e LOCAL_USERNAME=$(id -nu) -e LOCAL_UID=$(id -u) -e LOCAL_GID=$(id -g) -v ${PWD}:/shared -v ~/.ssh:/root/.ssh --network host -it --entrypoint /bin/bash $DOCKYMAN_IMAGE_NAME:$DOCKYMAN_VER
