{ pkgs ? import <nixpkgs> {} }:

with pkgs;

let
  packages = import ./nix/ganache/default.nix { };
  python = pkgs.python36;
  pythonPackages = python36Packages;
in
pkgs.buildEnv {
  name = "vagrant";
  paths = [
    packages.ganache-cli

    pythonPackages.celery
    pythonPackages.alembic

    nodejs-13_x
    redis
    postgresql_12
    ncurses

    terraform_0_12
    vagrant
  ];
}