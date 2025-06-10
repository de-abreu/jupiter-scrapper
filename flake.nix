{
  description = "Jupiter Scrapper Development Environment";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-25.05";

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};

    # Custom Python environment with dependencies
    pythonEnv = pkgs.python3.withPackages (ps:
      with ps; [
        beautifulsoup4
        selenium
        types-beautifulsoup4
      ]);
  in {
    # For `nix develop`
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [pythonEnv];
      shellHook = ''
        echo "🚀 Welcome to the Jupiter Scrapper dev environment!"
      '';
    };
  };
}
