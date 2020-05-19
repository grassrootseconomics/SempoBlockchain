{ pkgs ? import <nixpkgs> {} }:

let
  commitRev = "025deb80b2412e5b7e88ea1de631d1bd65af1840";
  nixpkgs = builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/${commitRev}.tar.gz";
    sha256 = "0wlhlmghfdvqqw2k7nyiiz4p9762aqbb2q88p6sswmlv499x5hb3";
  };
  pkgs = import nixpkgs { config = {}; };
in
pkgs.buildEnv {
  name = "build-env";
  paths = with pkgs; [
    docker
    docker_compose
    kubectl
    git
    awscli
    aws-iam-authenticator
  ];
}