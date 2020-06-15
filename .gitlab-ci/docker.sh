#!/usr/bin/env nix-shell
#!nix-shell -i bash -p docker git
set -o errexit -o nounset -o pipefail

build_image() {
  GIT_HASH=$1

  docker build -t server . -f ./app/Dockerfile --build-arg GIT_HASH=$GIT_HASH
  docker build -t eth_worker . -f ./eth_worker/Dockerfile --build-arg CONTAINER_TYPE=ANY_PRIORITY_WORKER
  docker build -t proxy ./proxy
  docker build -t pgbouncer . -f ./pgbouncer/Dockerfile
}

push_image() {
  TAG=$1

  docker tag server:latest ${REGISTRY}/server:${TAG}
  docker push ${REGISTRY}/server:${TAG}
  
  docker tag eth_worker:latest ${REGISTRY}/eth_worker:${TAG}
  docker push ${REGISTRY}/eth_worker:${TAG}

  docker tag pgbouncer:latest ${REGISTRY}/pgbouncer:${TAG}
  docker push ${REGISTRY}/pgbouncer:${TAG}
}

GIT_HASH=$(git rev-parse --short HEAD)
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

echo "Building git hash $GIT_HASH and branch name $BRANCH_NAME"

docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

if [ $BRANCH_NAME == "master" ]
then
  build_image $GIT_HASH
  push_image $GIT_HASH
else
  build_image $GIT_HASH
  push_image $GIT_HASH
fi
