#!/usr/bin/env bash

set -ex

./vagrant/generate_secrets.sh
./vagrant/node_install.sh
./vagrant/node_build.sh
./vagrant/docker_build.sh
./vagrant/docker_up.sh

set +ex
