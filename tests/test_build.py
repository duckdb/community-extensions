import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


BUILD_SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'build.py'


class DescriptorTests(unittest.TestCase):
    def parse(self, extension):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            descriptor = root / 'extensions' / 'example' / 'description.yml'
            descriptor.parent.mkdir(parents=True)
            descriptor.write_text(
                yaml.safe_dump(
                    {
                        'extension': {'name': 'example', **extension},
                        'repo': {'github': 'example/extension', 'ref': 'abc123'},
                    }
                )
            )
            result = subprocess.run(
                [sys.executable, str(BUILD_SCRIPT)],
                cwd=root,
                env={
                    **os.environ,
                    'ALL_CHANGED_FILES': str(descriptor),
                    'DUCKDB_VERSION': 'v1.5.5',
                    'DUCKDB_LATEST_STABLE': 'v1.5.5',
                },
                text=True,
                capture_output=True,
            )
            output = root / 'env.sh'
            return result, (
                dict(line.split('=', 1) for line in output.read_text().splitlines()) if output.exists() else {}
            )

    def test_existing_descriptors_default_to_binary_only(self):
        result, output = self.parse({})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output['COMMUNITY_EXTENSION_RELEASE_MATERIALS'], 'false')
        self.assertEqual(json.loads(output['COMMUNITY_EXTENSION_EXTRA_CONFIG']), '')
        self.assertEqual(output['COMMUNITY_EXTENSION_REF'], 'abc123')
        self.assertEqual(output['COMMUNITY_EXTENSION_DEPLOY'], '1')

    def test_multiline_config_stays_in_one_workflow_output(self):
        config = 'set(PACKAGE ON CACHE BOOL "Package materials" FORCE)\n# second line\n'
        result, output = self.parse(
            {
                'release_materials': True,
                'extra_extension_config': config,
                'excluded_platforms': 'wasm_mvp;wasm_eh;wasm_threads',
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output['COMMUNITY_EXTENSION_RELEASE_MATERIALS'], 'true')
        self.assertEqual(json.loads(output['COMMUNITY_EXTENSION_EXTRA_CONFIG']), config)

    def test_invalid_config_fails_before_emitting_outputs(self):
        for config in (
            {'release_materials': 'false'},
            {'release_materials': 1},
            {'extra_extension_config': []},
            {'release_materials': True},
            {'release_materials': True, 'excluded_platforms': 'wasm_mvp;wasm_eh'},
        ):
            with self.subTest(config=config):
                result, output = self.parse(config)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(output, {})


if __name__ == '__main__':
    unittest.main()
