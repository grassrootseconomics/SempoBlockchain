#!/usr/bin/env bash

apt-get update
apt-get install -y gcc g++ libffi-dev libstdc++-6-dev python3-dev musl-dev libssl-dev libmysqlclient-dev
apt-get remove python2.7
curl -L https://nixos.org/nix/install | sh
. /home/vagrant/.nix-profile/etc/profile.d/nix.sh
nix-channel --add https://nixos.org/channels/nixos-20.03 nixpkgs
nix-channel --update
nix-env -iA cachix -f https://cachix.org/api/v1/install
# cachix use sarafu-dev
# nix-env -if sarafu/default.nix
