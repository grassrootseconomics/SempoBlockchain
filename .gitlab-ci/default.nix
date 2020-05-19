{ pkgs ? import <nixpkgs> {} }:

let
  commitRev = "025deb80b2412e5b7e88ea1de631d1bd65af1840";
  nixpkgs = builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/${commitRev}.tar.gz";
    sha256 = "09mp6vqs0h71g27w004yrz1jxla31ihf18phw69wj61ix74ac4m0";
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
