import json
import os
import subprocess
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
	print("No changed files, only waddle will be built as a test")
	desc_files = ['extensions/waddle/description.yml']
	deploy = False

desc_file = desc_files[0]

with open(desc_file, 'r') as stream:
	desc = yaml.safe_load(stream)

print(desc)

# Validate that the directory name matches the extension name
dir_name = os.path.basename(os.path.dirname(desc_file))
extension_name = desc['extension']['name']
if dir_name != extension_name:
    raise ValueError(f"Directory name '{dir_name}' does not match extension name '{extension_name}' in {desc_file}. Please rename the directory to '{extension_name}'.")

# todo check other stuff like build system etc.

# returns the most recent commit to community-extensions relative to the current push / pull request
def base_commit():
	event_name = os.environ.get('GITHUB_EVENT_NAME')
	if event_name == 'pull_request':
		ref = os.environ.get('GITHUB_BASE_REF')
	elif event_name == 'push':
		with open(os.environ['GITHUB_EVENT_PATH']) as event:
			ref = json.load(event).get('before')
	else:
		return None

	if not ref or ref == '0' * 40:
		return None
	if subprocess.run(['git', 'fetch', '-q', '--depth', '1', 'origin', ref]).returncode != 0:
		return None

	return subprocess.run(['git', 'rev-parse', 'FETCH_HEAD'], capture_output=True, text=True).stdout.strip() or None

def repo_field_changed(field):
	base = base_commit()
	print(f"Comparing repo.{field} against base commit: {base}")

	if not base:
		return True
	base_desc = subprocess.run(['git', 'show', f'{base}:{desc_file}'], capture_output=True, text=True)
	if base_desc.returncode != 0:
		return True
	base_value = ((yaml.safe_load(base_desc.stdout) or {}).get('repo') or {}).get(field)

	field_changed = base_value is None or str(base_value) != str(desc['repo'].get(field))
	return field_changed

def select_ref(field):
	if field in desc['repo']:
		ref = desc['repo'][field]
		if not repo_field_changed(field):
			print(f"Skipping {field} build: repo.{field} is unchanged ({ref})")
			ref = None
	else:
		print(f"Skipping {field} build: repo.{field} is not defined")
		ref = None

	return ref

with open('env.sh', 'w+') as hdl:
	hdl.write(f"COMMUNITY_EXTENSION_GITHUB={desc['repo']['github']}\n")
	build_directory = desc['repo'].get('build_directory')
	if build_directory:
		hdl.write(f"COMMUNITY_EXTENSION_BUILD_DIRECTORY={build_directory}\n")
	if 'canonical_name' in desc.get('repo', {}):
		hdl.write(f"COMMUNITY_EXTENSION_CANONICAL_NAME={desc['repo']['canonical_name']}\n")

	extension_ref = None
	if os.environ['DUCKDB_VERSION'] == os.environ['DUCKDB_LATEST_STABLE']:
		extension_ref = select_ref('ref');
	elif os.environ['DUCKDB_VERSION'] == 'v1.4.5':
		extension_ref = select_ref('andium');
	elif os.environ['DUCKDB_VERSION'] == 'v1.5.6':
		extension_ref = select_ref('variegata');
	elif os.environ['DUCKDB_VERSION'] == 'v2.0.0-alpha': # placeholder
		extension_ref = select_ref('ref_next');
	else:
		print("No valid ")

	if extension_ref:
		hdl.write(f"COMMUNITY_EXTENSION_REF={extension_ref}\n")
	hdl.write(f"COMMUNITY_EXTENSION_NAME={desc['extension']['name']}\n")
	excluded_platforms = desc['extension'].get('excluded_platforms')
	opt_in_platforms = desc['extension'].get('opt_in_platforms')
	requires_toolchains = desc['extension'].get('requires_toolchains')
	custom_toolchain_script = desc['extension'].get('custom_toolchain_script')
	vcpkg_url = desc['extension'].get('vcpkg_url')
	vcpkg_commit = desc['extension'].get('vcpkg_commit')
	test_config = desc['extension'].get('test_config')
	skip_tests = desc['extension'].get('skip_tests')
	extra_extension_config = desc['extension'].get('extra_extension_config')
	cuda_archs = desc['extension'].get('cuda_archs')
	cuda_version = desc['extension'].get('cuda_version')
	use_merged_vcpkg_manifest = desc['extension'].get('use_merged_vcpkg_manifest')
	if excluded_platforms:
		hdl.write(f"COMMUNITY_EXTENSION_EXCLUDE_PLATFORMS={excluded_platforms}\n")
	if opt_in_platforms:
		hdl.write(f"COMMUNITY_EXTENSION_OPT_IN_PLATFORMS={opt_in_platforms}\n")
	if requires_toolchains:
		hdl.write(f"COMMUNITY_EXTENSION_REQUIRES_TOOLCHAINS={requires_toolchains}\n")
	if vcpkg_url:
		hdl.write(f"COMMUNITY_EXTENSION_VCPKG_URL={vcpkg_url}\n")
	if vcpkg_commit:
		hdl.write(f"COMMUNITY_EXTENSION_VCPKG_COMMIT={vcpkg_commit}\n")
	if deploy:
		hdl.write(f"COMMUNITY_EXTENSION_DEPLOY=1\n")
	if test_config:
		escaped_config =test_config.replace("\n", "")
		hdl.write(f"COMMUNITY_EXTENSION_TEST_CONFIG={escaped_config}\n")
	if skip_tests:
		hdl.write("COMMUNITY_EXTENSION_SKIP_TESTS=1\n")
	if extra_extension_config:
		hdl.write("COMMUNITY_EXTENSION_EXTRA_CONFIG<<EOF\n")
		hdl.write(f"{extra_extension_config.rstrip()}\n")
		hdl.write("EOF\n")
	if cuda_archs:
		hdl.write(f"COMMUNITY_EXTENSION_CUDA_ARCHS={cuda_archs}\n")
	if cuda_version:
		hdl.write(f"COMMUNITY_EXTENSION_CUDA_VERSION={cuda_version}\n")
	if use_merged_vcpkg_manifest:
		hdl.write("COMMUNITY_EXTENSION_USE_MERGED_VCPKG_MANIFEST=1\n")
