import os
import sys
import yaml
import subprocess

desc_file = sys.argv[1]
duckdb = sys.argv[2]

with open(desc_file, 'r') as stream:
	desc = yaml.safe_load(stream)

subprocess.run(["gh", "api", "https://api.github.com/repos/" + desc['repo']['github'], "--jq=.stargazers_count"])
