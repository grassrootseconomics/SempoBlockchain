with import <nixpkgs> { };

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
stdenv.mkDerivation {
  name = "dev";
  buildInputs = [ (import ./default.nix { inherit pkgs; }) ] ++ [
    python
    pythonPackages.pip
    pythonPackages.setuptools
    pythonPackages.virtualenvwrapper
    pythonPackages.pandas
  ];
  shellHook = "
    export PYTHONPATH=`pwd`/venv/${python.sitePackages}/:$PYTHONPATH
    setup() {
      virtualenv venv
    }
    pip-install() {
      cd app
      python3 -m pip install -r slow_requirements.txt
      python3 -m pip install -r requirements.txt
      cd ../eth_worker
      python3 -m pip install -r requirements.txt
      cd ../worker
      python3 -m pip install -r requirements.txt
      cd ../test
      python3 -m pip install -r requirements.txt
    }
    export SOURCE_DATE_EPOCH=315532800
  ";
}
