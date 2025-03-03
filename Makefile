run:
	nix --extra-experimental-features 'nix-command flakes' run

draw:
	nix --extra-experimental-features 'nix-command flakes' run .#draw
