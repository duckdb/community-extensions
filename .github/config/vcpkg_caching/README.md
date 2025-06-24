# VCPKG caching
To speed up the performance of community extension builds, we autogenerate a list of vcpkg dependencies who's binaries we'd like to cache.
For this the generated_list.json file is used. This file can be automatically updated by running:

```sh
python3 -m venv venv
. ./venv/bin/activate
python3 -m pip install requests pyyaml GitPython 
python3 scripts/parse_vcpkg_deps.py
```

To add additional excludes, edit the `.github/config/vcpkg_caching/manual_excludes.json` file manually and rerun the script.