#!/usr/bin/env python3
import os
import json
import tempfile
import argparse
from git import Repo
from pathlib import Path
import yaml
import requests

def parse_vcpkg_deps(repo_url, git_ref):
    """Download and parse vcpkg.json dependencies"""
    deps = set()
    try:
        # Form raw GitHub content URL
        org_repo = repo_url.replace('https://github.com/', '')
        raw_url = f"https://raw.githubusercontent.com/{org_repo}/{git_ref}/vcpkg.json"

        response = requests.get(raw_url)
        if response.status_code == 404:
            return deps
        response.raise_for_status()

        vcpkg_data = response.json()
        if "dependencies" in vcpkg_data:
            # Add both simple dependencies and features
            for dep in vcpkg_data["dependencies"]:
                if isinstance(dep, str):
                    deps.add(dep)
                elif isinstance(dep, dict) and "name" in dep:
                    deps.add(dep["name"])
    except Exception as e:
        print(f"Error processing {repo_url} at {git_ref}: {str(e)}")
    return deps

def generate_list_of_vcpkg_deps():
    extensions_dir = Path('./extensions')
    repo_list = []

    # Iterate through all description.yml files in extensions directory 
    for desc_file in extensions_dir.glob('*/description.yml'):
        with open(desc_file) as f:
            try:
                desc = yaml.safe_load(f)
                if 'repo' in desc:
                    repo_url = f"https://github.com/{desc['repo']['github']}"
                    ref = desc['repo']['ref']
                    excluded = desc.get('extension', {}).get('excluded_platforms')
                    repo_list.append((repo_url, ref, excluded))
            except Exception as e:
                print(f"Error parsing {desc_file}: {str(e)}")

    return repo_list

def get_duckdb_archs():
    """Fetch and parse distribution matrix to get architecture list"""
    try:
        url = "https://raw.githubusercontent.com/duckdb/extension-ci-tools/main/config/distribution_matrix.json"
        response = requests.get(url)
        response.raise_for_status()
        matrix = response.json()

        archs = set()
        for platform in matrix.values():
            for config in platform["include"]:
                archs.add(config["duckdb_arch"])
        return archs

    except Exception as e:
        print(f"Error fetching distribution matrix: {str(e)}")
        return set()

def is_excluded_for_arch(dep_excluded_platforms, arch):
    """Check if dependency is excluded for given architecture"""
    return dep_excluded_platforms and arch in dep_excluded_platforms


def merge_excluded_platforms(platforms_list):
    """Merge excluded platforms keeping only shared ones"""
    if not platforms_list:
        return None
    if None in platforms_list:
        return None
    # Convert string platforms to sets
    platform_sets = [set(p.split(';')) if p else set() for p in platforms_list]
    # Return intersection of all platform sets
    return set.intersection(*[s for s in platform_sets if s])


def get_deps_for_arch(deps, arch):
    """Get list of dependencies for specific architecture"""
    return [dep for dep, excluded in deps.items() if not is_excluded_for_arch(excluded, arch)]


def parse_manual_excludes(exclude_file):
    """Parse manual exclusions JSON file"""
    try:
        with open(exclude_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error parsing manual excludes file: {str(e)}")
        return {}


def filter_manual_excludes(deps_list, arch, manual_excludes):
    """Filter out manually excluded dependencies for given architecture"""
    if arch in manual_excludes:
        return [dep for dep in deps_list if dep not in manual_excludes[arch]]
    return deps_list


def write_deps_to_json(archs, deps, output_file, exclude_file=None, excluded_platforms=None):
    """Write dependencies to JSON file"""
    manual_excludes = parse_manual_excludes(exclude_file) if exclude_file else {}

    output = {}
    for arch in sorted(archs):
        if excluded_platforms and arch in excluded_platforms:
            output[arch] = []
            continue
        arch_deps = get_deps_for_arch(deps, arch)
        arch_deps = filter_manual_excludes(arch_deps, arch, manual_excludes)
        output[arch] = sorted(arch_deps)
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', help='Output JSON file path', default='./.github/config/vcpkg_caching/generated_dep_list.json')
    parser.add_argument('--exclude', help='Manual exclude list', default='./.github/config/vcpkg_caching/manual_excludes.json')
    parser.add_argument('--exclude-platform', help='Platform to fully exclude from dependency list', nargs='+')

    args = parser.parse_args()

    archs = get_duckdb_archs()
    print("Available architectures:", ';'.join(sorted(archs)))

    list = generate_list_of_vcpkg_deps()
    all_deps = []

    # Collect all dependencies 
    for repo in list:
        deps = parse_vcpkg_deps(repo[0], repo[1])
        all_deps.append((deps, repo[2]))

    # Merge duplicate dependencies
    merged_deps = {}
    for deps, excluded in all_deps:
        for dep in deps:
            if dep not in merged_deps:
                merged_deps[dep] = []
            merged_deps[dep].append(excluded)

    # Consolidate excluded platforms
    final_deps = {dep: merge_excluded_platforms(platforms) for dep, platforms in merged_deps.items()}
    
    

    # Write to JSON file
    write_deps_to_json(archs, final_deps, args.output, args.exclude, args.exclude_platform)
    print(f"\nDependencies written to {args.output}")


if __name__ == "__main__":
    main()
