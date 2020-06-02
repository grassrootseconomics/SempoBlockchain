#!/usr/bin/env bash

[ ! -d config_files/secret ] && mkdir config_files/secret
cd config_files
python3 generate_secrets.py -n docker_test
