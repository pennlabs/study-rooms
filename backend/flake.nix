{
  description = "A basic flake using pyproject.toml project metadata";

  # This dictionary version controls external inputs to this Flake as described in https://wiki.nixos.org/wiki/Flakes#Flake_schema
  inputs = {
      # firebase-admin was just added to nixpkgs. Should move this to stable later.
      nixpkgs.url = "github:NixOS/nixpkgs?rev=dd1519d642dec465aceae674c96d4cee288dc910";
      # Tool for making packing pyproject.yaml and Poetry projects. Documented at https://pyproject-nix.github.io/pyproject.nix/introduction.html
      pyproject-nix = {
          url =  "github:pyproject-nix/pyproject.nix";
          inputs.nixpkgs.follows = "nixpkgs";
      };
      # Not yet merged
      django-runtime-options = {
          url = "github:clay53/django-runtime-options";
      };
      # Not yet merged
      django-labs-accounts = {
          url = "github:clay53/django-labs-accounts";
      };
      # Not in nixpkgs. Dependency of this project
      apns2 = {
          url = "github:Pr0Ger/PyAPNs2";
          flake = false;
      };
      # Not in nixpkgs. Dependency of apns2
      hyper = {
          url = "github:python-hyper/hyper";
          flake = false;
      };
      # Not in nixpkgs. Dependency of this project
      alt-profanity-check = {
          url = "github:dimitrismistriotis/alt-profanity-check";
          flake = false;
      };
  };

  outputs =
    { nixpkgs, pyproject-nix, django-labs-accounts, django-runtime-options, apns2, hyper, alt-profanity-check, ... }:
    let
      # Loads pyproject.toml into a high-level project representation. Documented at: https://pyproject-nix.github.io/pyproject.nix/lib/project.html
      project = pyproject-nix.lib.project.loadPyproject {
        projectRoot = ./.;
      };

      # Only configuring x86_64-linux
      pkgs = nixpkgs.legacyPackages.x86_64-linux;

      # Define Python interpreter version and package sources
      python = pkgs.python312.override {
        packageOverrides = self: prev: {
            django = prev.django_5;
            django-labs-accounts = django-labs-accounts.packages.x86_64-linux.default;
            django-runtime-options = django-runtime-options.packages.x86_64-linux.buildWithOverrides prev.buildPythonPackage prev.django_5;
            django-extensions = prev.django-extensions.overridePythonAttrs {
                # Tests fail due to slight incompatibility with Django 5: https://github.com/django-extensions/django-extensions/issues/1885 . This "fix" also used in https://github.com/NixOS/nixpkgs/blob/1da52dd49a127ad74486b135898da2cef8c62665/pkgs/by-name/pr/pretalx/package.nix#L33
                doCheck = false;
            };
            apns2 = prev.buildPythonPackage (
                let project =
                    pyproject-nix.lib.project.loadPoetryPyproject {
                        projectRoot = apns2;
                    };
                in
                project.renderers.buildPythonPackage { inherit python; }
            );
            hyper = prev.buildPythonPackage {
                pname = "hyper";
                version = "0.7.0";
                
                propagatedBuildInputs = [
                    prev.hyperframe
                    prev.brotlipy
                    prev.rfc3986
                    prev.h2
                ];

                src = hyper;
            };
            alt-profanity-check = prev.buildPythonPackage {
                pname = "alt-profanity-check";
                version = "1.6.1";
                
                propagatedBuildInputs = [
                    prev.scikit-learn
                    prev.joblib
                ];

                src = alt-profanity-check;
            };
        };
      };
    in
    {
      # Create a development shell containing dependencies from `pyproject.toml`
      devShells.x86_64-linux.default =
        let
          # Returns a function that can be passed to `python.withPackages`
          arg = project.renderers.withPackages {
              inherit python;
              # Function from python interpreter package set to extra packages
              extraPackages = py: [
                # dev dependencies don't seem to be automatically added
                py.django-extensions
              ];
          };

          # Returns a wrapped environment (virtualenv like) with all our packages
          pythonEnv = python.withPackages arg;

        in
        # Create a devShell like normal.
        pkgs.mkShell { packages = [ pythonEnv ]; };
    };
}
