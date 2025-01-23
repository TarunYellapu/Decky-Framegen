#!/usr/bin/env bash

# Remove /home/deck/fgmod directory if it exists
if [[ -d "/home/deck/fgmod" ]]; then
    rm -rf "/home/deck/fgmod"
fi

# Remove specific files from ~/Downloads if they exist
downloads_dir="$HOME/Downloads"
files_to_remove=("prepare.sh" "fgmod.sh" "fgmod-uninstaller.sh")

for file in "${files_to_remove[@]}"; do
    if [[ -f "$downloads_dir/$file" ]]; then
        rm "$downloads_dir/$file"
    fi
done

echo "FGmod removed"