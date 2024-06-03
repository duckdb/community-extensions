import os
import yaml

# TODO: check prefix, needs to be in installation dir

desc_files = os.environ['ALL_CHANGED_FILES'].split(' ')
if len(desc_files) != 1:
	raise ValueError('cannot have multiple descriptors changed or packages with spaces in their names')
desc_file = desc_files[0]

with open(desc_file, 'r') as stream:
    desc = yaml.safe_load(stream)

print(desc)

# todo check other stuff like build system etc.


os.environ['COMMUNITY_EXTENSION_GITHUB'] = desc['repo']['github']
os.environ['COMMUNITY_EXTENSION_REF'] = desc['repo']['ref']
os.environ['COMMUNITY_EXTENSION_NAME'] = desc['extension']['name']