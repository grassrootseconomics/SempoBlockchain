with import <nixpkgs> { };

let
  python = pkgs.python36;
  pythonPackages = python36Packages;
in
stdenv.mkDerivation {
  name = "dev";
  buildInputs = [ (import ./default.nix { inherit pkgs; }) ] ++ [
    redis-desktop-manager
    pgadmin
    python
    pythonPackages.pip
    pythonPackages.setuptools
    pythonPackages.virtualenvwrapper
    pythonPackages.pandas
    libmysqlclient
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

# nix-build default.nix | cachix push sarafu-dev
# cachix use sarafu-dev
