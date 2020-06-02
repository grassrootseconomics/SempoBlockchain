#!/usr/bin/env bash

docker build -t server . -f ./app/Dockerfile #--build-arg GIT_HASH=$CIRCLE_SHA1
docker build -t eth_worker . -f ./eth_worker/Dockerfile --build-arg CONTAINER_TYPE=ANY_PRIORITY_WORKER

docker build -t proxy ./proxy
docker build -t pgbouncer . -f ./pgbouncer/Dockerfile
