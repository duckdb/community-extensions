#!/usr/bin/env bash

set -euo pipefail

trap cleanup SIGINT SIGTERM

cleanup() {
    trap - SIGINT SIGTERM
    echo "Script interrupted"
    exit 1
}


if [ $# -lt 1 ]; then
    echo "Usage: ./scripts/fetch_extensions.sh path_to_duckdb_binary [path_to_duckdb_binary...]"
    echo "Each extension is installed with the first binary (pass the newest DuckDB version first) it is available for"
    exit 1
fi

rm -rf build
for extension_folder in extensions/*;
do
    extension_name=$(basename -- $extension_folder)
    echo "Installing $extension_name"
    installed=false
    for binary in "$@"; do
        if $binary -c "SET extension_directory = 'build/extension_dir'; FORCE INSTALL '$extension_name' FROM community;" 2>/dev/null; then
            echo "Installed $extension_name using $binary"
            installed=true
            break
        fi
    done
    $installed || echo "Missing $extension_name"
done
