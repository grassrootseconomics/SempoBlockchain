#!/usr/bin/env bash

sudo apt-get update
sudo apt-get install -y gcc g++ libffi-dev libstdc++-6-dev python3-dev python3-pip musl-dev libssl-dev libmysqlclient-dev
sudo apt-get remove python -y
#echo 'alias python=python3\nalias pip=pip3' >> /home/vagrant/.bash_aliases
curl -L https://nixos.org/nix/install | sh
. /home/vagrant/.nix-profile/etc/profile.d/nix.sh
nix-channel --add https://nixos.org/channels/nixos-20.03 nixpkgs
nix-channel --update
nix-env -iA cachix -f https://cachix.org/api/v1/install
# cachix use sarafu-dev
# nix-env -if sarafu/default.nix
