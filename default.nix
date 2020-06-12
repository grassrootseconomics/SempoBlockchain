{ pkgs ? import <nixpkgs> {} }:

# nix-build default.nix | cachix push sarafu-dev
# cachix use sarafu-dev

let
  commitRev = "025deb80b2412e5b7e88ea1de631d1bd65af1840";
  nixpkgs = builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/${commitRev}.tar.gz";
    sha256 = "09mp6vqs0h71g27w004yrz1jxla31ihf18phw69wj61ix74ac4m0";
  };
  pkgs = import nixpkgs { config = {}; };
  python = pkgs.python36;
  pythonPackages = pkgs.python36Packages;
in
pkgs.buildEnv {
  name = "vagrant";
  paths = with pkgs; [
    git
    docker
    docker_compose
    nodejs-13_x
    redis
    postgresql_12
    ncurses
    terraform_0_12
    vagrant
  ];
}