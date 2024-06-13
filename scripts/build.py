import os
import yaml

# TODO: check prefix, needs to be in installation dir

desc_files = os.environ['ALL_CHANGED_FILES'].split(' ')
if len(desc_files) != 1:
	raise ValueError('cannot have multiple descriptors changed or packages with spaces in their names')
desc_file = desc_files[0]
if len(desc_file) == 0:
	raise ValueError('description file not found (ALL_CHANGED_FILES was set but empty)')

with open(desc_file, 'r') as stream:
    desc = yaml.safe_load(stream)

print(desc)

# todo check other stuff like build system etc.

with open('env.sh', 'w+') as hdl:
	hdl.write(f"COMMUNITY_EXTENSION_GITHUB={desc['repo']['github']}\n")
	hdl.write(f"COMMUNITY_EXTENSION_REF={desc['repo']['ref']}\n")
	hdl.write(f"COMMUNITY_EXTENSION_NAME={desc['extension']['name']}\n")
