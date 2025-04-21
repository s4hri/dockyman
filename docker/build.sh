set -a ; . ./build.env ; set +a

sed -i "s/^DOCKYMAN_VER=.*/DOCKYMAN_VER=$DOCKYMAN_VER/" ../dockyman/model/dockyman.env
sed -i "s/^DOCKYMAN_VER=.*/DOCKYMAN_VER=$DOCKYMAN_VER/" ../dockyman/model/.dockyman_installer/dockyman.sh
cp ../README.md ../dockyman/model/README.md

docker build -t $DOCKYMAN_IMAGE_NAME:$DOCKYMAN_VER --build-arg DOCKYMAN_VER=$DOCKYMAN_VER -f Dockerfile ..
