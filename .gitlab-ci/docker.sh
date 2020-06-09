#!/usr/bin/env nix-shell
#!nix-shell -i bash -p docker
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

  docker tag server:latest grassrootseconomics/server:${TAG}
  docker push grassrootseconomics/server:${TAG}
  
  docker tag eth_worker:latest grassrootseconomics/eth_worker:${TAG}
  docker push grassrootseconomics/eth_worker:${TAG}

  docker tag pgbouncer:latest grassrootseconomics/pgbouncer:${TAG}
  docker push grassrootseconomics/pgbouncer:${TAG}
}

GIT_HASH=$(git rev-parse --short HEAD)
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

# push_image $GIT_HASH
if [ $BRANCH_NAME == "master" ]
then
  build_image $GIT_HASH
  push_image $GIT_HASH
else
  build_image $GIT_HASH
fi
