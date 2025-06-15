#!/usr/bin/env bash

set -euo pipefail

trap cleanup SIGINT SIGTERM

cleanup() {
    trap - SIGINT SIGTERM
    echo "Script interrupted"
    exit 1
}


if [ $# -lt 1 ]; then
    echo "Usage: ./scripts/fetch_extensions.sh path_to_duckdb_binary"
    exit 1
fi

rm -rf build
for extension_folder in extensions/*;
do
    extension_name=$(basename -- $extension_folder)
    echo "Installing $extension_name"
    $1 -c "SET extension_directory = 'build/extension_dir'; FORCE INSTALL '$extension_name' FROM community;" || echo "Missing $extension_name"
done
