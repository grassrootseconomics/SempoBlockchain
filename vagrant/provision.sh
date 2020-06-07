#!/usr/bin/env bash

sudo apt-get update
sudo apt-get install -y gcc g++ libffi-dev libstdc++-6-dev python3-dev python3-pip musl-dev libssl-dev libmysqlclient-dev
sudo apt-get remove python -y

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

nvm install 10.16.0
nvm use 10.16.0
node -v

curl -L https://nixos.org/nix/install | sh
. /home/vagrant/.nix-profile/etc/profile.d/nix.sh
nix-channel --add https://nixos.org/channels/nixos-20.03 nixpkgs
nix-channel --update

# Search for packages you'd like to install here https://nixos.org/
nix-env -iA nixpkgs.docker-compose nixpkgs.ripgrep

# nix-env -iA cachix -f https://cachix.org/api/v1/install
# cachix use sarafu-dev
# nix-env -if sarafu/default.nix
