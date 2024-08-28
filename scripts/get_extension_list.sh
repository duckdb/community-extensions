set -eo pipefail

echo -n "EXTENSION_LIST=[" > extension_list
for extension_folder in extensions/*;
do
    extension_name=$(basename -- $extension_folder)
    echo -n "'$extension_name'," >> extension_list
done
echo "]" >> extension_list
