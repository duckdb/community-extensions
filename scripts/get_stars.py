import os
import sys
import yaml
import subprocess

desc_file = sys.argv[1]
duckdb = sys.argv[2]

with open(desc_file, 'r') as stream:
	desc = yaml.safe_load(stream)

subprocess.run([duckdb, "-c", "COPY (SELECT ' ') TO 'build/stars.csv' (HEADER FALSE);"])
subprocess.run([duckdb, "-c", "COPY (SELECT stargazers_count FROM read_json('https://api.github.com/repos/" + desc['repo']['github'] + "')) TO 'build/stars.csv' (HEADER FALSE);"])
subprocess.run(["cat", "build/stars.csv"])
