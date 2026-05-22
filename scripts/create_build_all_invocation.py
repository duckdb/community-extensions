# WHAT'S THIS?
#
#   > A script to split up the workflow invocation in more manageable chunks to avoid overloading the GitHub UIs
#
# HOW TO USE
#
#   > python3 scripts/create_build_all_invocation.py --batch_size=5 --duckdb_tag=v1.4.1 --duckdb_version=b390a7c3760bd95926fe8aefde20d04b349b472e
#

import argparse
import json
import subprocess
from math import ceil
import glob
import yaml


def read_extension_list():
    extensions = []
    for path in glob.glob('./extensions/*/description.yml'):
        with open(path) as f:
            desc = yaml.safe_load(f)
            extensions.append(desc['extension']['name'])
    return extensions


def split_into_batches(lst, batch_size):
    return [lst[i:i + batch_size] for i in range(0, len(lst), batch_size)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duckdb_version', type=str, help='DuckDB version hash', required=True)
    parser.add_argument('--duckdb_tag', type=str, help='DuckDB version tag', required=True)

    # Number of extensions to build per workflow invocation
    parser.add_argument('--batch_size', type=int, help='Number of extensions per invocation', required=False, default=10)

    args = parser.parse_args()

    extensions = read_extension_list()
    batches = split_into_batches(extensions, args.batch_size)

    for batch in batches:
        json_str = json.dumps(batch).replace('"', "'")
        cmd = f'gh workflow run build_all.yml -f build_extensions=\"{json_str}\" -f duckdb_version={args.duckdb_version} -f duckdb_tag={args.duckdb_tag} -f deploy=true'
        print(cmd)

if __name__ == '__main__':
    main()
