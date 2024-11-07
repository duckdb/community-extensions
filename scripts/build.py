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

deploy = True

if len(desc_files) == 0 or len(desc_files[0]) == 0:
	print("No changed files, only quack will be built as a test")
	desc_files = ['extensions/quack/description.yml']
	deploy = False

desc_file = desc_files[0]

with open(desc_file, 'r') as stream:
	desc = yaml.safe_load(stream)

print(desc)

# todo check other stuff like build system etc.

with open('env.sh', 'w+') as hdl:
	hdl.write(f"COMMUNITY_EXTENSION_GITHUB={desc['repo']['github']}\n")
	extension_ref = desc['repo']['ref']
	if  os.environ['DUCKDB_VERSION'] != os.environ['DUCKDB_LATEST_STABLE']:
		if 'ref_next' in desc['repo']:
			extension_ref = desc['repo']['ref_next']
	hdl.write(f"COMMUNITY_EXTENSION_REF={extension_ref}\n")
	hdl.write(f"COMMUNITY_EXTENSION_NAME={desc['extension']['name']}\n")
	excluded_platforms = desc['extension'].get('excluded_platforms')
	requires_toolchains = desc['extension'].get('requires_toolchains')
	custom_toolchain_script = desc['extension'].get('custom_toolchain_script')
	vcpkg_url = desc['extension'].get('vcpkg_url')
	vcpkg_commit = desc['extension'].get('vcpkg_commit')
	if excluded_platforms:
		hdl.write(f"COMMUNITY_EXTENSION_EXCLUDE_PLATFORMS={excluded_platforms}\n")
	if requires_toolchains:
		hdl.write(f"COMMUNITY_EXTENSION_REQUIRES_TOOLCHAINS={requires_toolchains}\n")
	if vcpkg_url:
		hdl.write(f"COMMUNITY_EXTENSION_VCPKG_URL={vcpkg_url}\n")
	if vcpkg_commit:
		hdl.write(f"COMMUNITY_EXTENSION_VCPKG_COMMIT={vcpkg_commit}\n")
	if deploy:
		hdl.write(f"COMMUNITY_EXTENSION_DEPLOY=1\n")
