{
  description = "Jupiter Scrapper Development Environment";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-25.05";

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};

    # Custom Python environment
    pythonEnv = pkgs.python3.withPackages (ps:
      with ps; [
        beautifulsoup4
        selenium
        tabulate
        types-beautifulsoup4
      ]);
    chromeDeps = with pkgs; [chromium chromedriver];
    dependencies = [pythonEnv] ++ chromeDeps;

    # Script to run the Python app with arguments
    runScript = pkgs.writeShellScriptBin "jupiter-scrapper" ''
      ${pythonEnv}/bin/python src/main.py "$@"
    '';
  in {
    # For `nix develop`
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = dependencies;
      shellHook = ''
        echo "🚀 Welcome to the Jupiter Scrapper dev environment!"
      '';
    };

    # For `nix run`
    apps.${system} = {
      default = {
        type = "app";
        program = "${runScript}/bin/jupiter-scrapper";
      };
    };
  };
}
