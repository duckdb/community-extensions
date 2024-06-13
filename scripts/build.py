import os
import sys
import yaml

# TODO: check prefix, needs to be in installation dir

if 'ALL_CHANGED_FILES' in os.environ:
	desc_files = os.environ['ALL_CHANGED_FILES'].split(' ')
else:
	desc_files = []

print(f"Files changed: {desc_files}")

if len(desc_files) > 1:
	raise ValueError('cannot have multiple descriptors changed or packages with spaces in their names')

if len(desc_files) == 0 or len(desc_files[0]) == 0:
	print("No changed files, nothing will be built")
	with open('env.sh', 'w+') as hdl:
		hdl.write(f"COMMUNITY_EXTENSION_GITHUB=\n")
		hdl.write(f"COMMUNITY_EXTENSION_REF=\n")
		hdl.write(f"COMMUNITY_EXTENSION_NAME=\n")
		sys.exit(os.EX_OK)

desc_file = desc_files[0]

with open(desc_file, 'r') as stream:
	desc = yaml.safe_load(stream)

print(desc)

# todo check other stuff like build system etc.

with open('env.sh', 'w+') as hdl:
	hdl.write(f"COMMUNITY_EXTENSION_GITHUB={desc['repo']['github']}\n")
	hdl.write(f"COMMUNITY_EXTENSION_REF={desc['repo']['ref']}\n")
	hdl.write(f"COMMUNITY_EXTENSION_NAME={desc['extension']['name']}\n")
