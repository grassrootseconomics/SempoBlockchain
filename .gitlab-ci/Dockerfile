FROM nixos/nix

RUN nix-channel --add https://nixos.org/channels/nixos-20.03 nixpkgs
RUN nix-channel --update

RUN nix-env -ibA nixpkgs.git
RUN nix-env -ibA cachix -f https://cachix.org/api/v1/install

COPY . ./

CMD ["true"]