#!/usr/bin/env nix-shell
#!nix-shell --pure -i bash --keep DOCKER_HOST --keep DOCKER_DRIVER --keep AWS_ACCESS_KEY_ID --keep AWS_SECRET_ACCESS_KEY --keep AWS_REGION ../shell.nix

set -ex

FILE=.envrc
if [ -f "$FILE" ]; then
    echo "Sourcing $FILE"
    source .envrc
else 
    echo "$FILE does not exist."
fi

unset APP_DB
export CONTAINER_MODE=TEST

alias python=python3
alias pip=pip3

[ -d './pipeline' ] && rm -Rf ./pipeline
git clone . ./pipeline
pushd ./pipeline

./vagrant/generate_secrets.sh
./vagrant/node_install.sh
./vagrant/node_build.sh
./vagrant/docker_build.sh
./vagrant/test_backend.sh
./vagrant/test_frontend.sh

popd
[ -d './pipeline' ] && rm -Rf ./pipeline

set +ex
