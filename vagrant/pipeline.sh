#!/usr/bin/env bash

set -ex

source .envrc
alias python=python3
alias pip=pip3

[ -d '../test' ] && rm -Rf ../test
git clone . ../test
pushd ../test

./vagrant/generate_secrets.sh
./vagrant/node_install.sh
./vagrant/node_build.sh
./vagrant/docker_build.sh
./vagrant/test_backend.sh
./vagrant/test_frontend.sh

popd

set +ex
