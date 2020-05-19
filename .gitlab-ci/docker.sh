#!/usr/bin/env nix-shell
#!nix-shell -i bash -p docker awscli aws-iam-authenticator
set -o errexit -o nounset -o pipefail

ensure_repo_exists() {
  for REPO_NAME in $1
  do
    aws ecr describe-repositories --repository-names $REPO_NAME --region $AWS_REGION || aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION
  done
}

build_image() {
  docker build -t server . -f ./app/Dockerfile --build-arg GIT_HASH=$CIRCLE_SHA1
  docker build -t eth_worker . -f ./eth_worker/Dockerfile --build-arg CONTAINER_TYPE=ANY_PRIORITY_WORKER
  docker build -t proxy ./proxy
  docker build -t pgbouncer . -f ./pgbouncer/Dockerfile
}

push_image() {
  eval $(aws ecr get-login --no-include-email --region $AWS_REGION);
  ensure_repo_exists "$CI_PROJECT_NAME"

  docker tag server:latest ${CI_PROJECT_NAME}:server_${CIRCLE_SHA1}
  docker push ${CI_PROJECT_NAME}:server_${CIRCLE_SHA1}
  docker tag proxy:latest ${CI_PROJECT_NAME}:proxy_${CIRCLE_SHA1}
  docker push ${CI_PROJECT_NAME}:proxy_${CIRCLE_SHA1}
  docker tag eth_worker:latest ${CI_PROJECT_NAME}:eth_worker_${CIRCLE_SHA1}
  docker push ${CI_PROJECT_NAME}:eth_worker_${CIRCLE_SHA1}
  docker tag pgbouncer:latest ${CI_PROJECT_NAME}:pgbouncer_${CIRCLE_SHA1}
  docker push ${CI_PROJECT_NAME}:pgbouncer_${CIRCLE_SHA1}
}

if [ $BRANCH_NAME == "master" ]
then
  build_image
  push_image
else
  build_image
fi
