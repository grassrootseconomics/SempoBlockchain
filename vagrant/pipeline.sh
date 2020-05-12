#!/usr/bin/env bash

set -ex

./vagrant/generate_secrets.sh
./vagrant/node_install.sh
./vagrant/node_build.sh
./vagrant/docker_build.sh
./vagrant/test_backend.sh
./vagrant/test_frontend.sh

set +ex
