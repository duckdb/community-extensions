set -eo pipefail

rm -rf build
for extension_folder in extensions/*;
do
    extension_name=$(basename -- $extension_folder)
    echo "Installing $extension_name"
    $1 -c "SET extension_directory = 'build/extension_dir'; FORCE INSTALL '$extension_name' FROM community;" || echo "Missing $extension_name"
done
