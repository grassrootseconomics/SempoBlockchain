{ pkgs ? import <nixpkgs> {} }:

with pkgs;

mkShell {
  buildInputs = [ (import ./default.nix { inherit pkgs; }) ];
}
