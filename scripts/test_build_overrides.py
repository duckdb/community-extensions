"""Regression checks for building against arbitrary DuckDB version overrides.

Run with: python -m unittest discover -s scripts -p 'test_build_overrides.py'
Requires PyYAML, like scripts/build.py.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class BuildOverrideTests(unittest.TestCase):
    def prepare(self, descriptor, version):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "extensions" / descriptor["extension"]["name"] / "description.yml"
            path.parent.mkdir(parents=True)
            path.write_text(yaml.safe_dump(descriptor))
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build.py")],
                cwd=directory,
                env={
                    **os.environ,
                    "GITHUB_EVENT_NAME": "workflow_dispatch",
                    "ALL_CHANGED_FILES": str(path.relative_to(directory)),
                    "DUCKDB_VERSION": version,
                    "DUCKDB_LATEST_STABLE": "v2.0.0",
                },
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return (Path(directory) / "env.sh").read_text().splitlines()

    def test_release_ref_selection(self):
        refs = {"ref": "1" * 40, "andium": "2" * 40, "variegata": "3" * 40, "ref_next": "4" * 40}
        descriptor = {
            "extension": {"name": "example"},
            "repo": {"github": "example/extension", **refs},
        }
        for version, field in [
            ("v2.0.0", "ref"),
            ("v2.0.1", "ref"),
            ("v100.10.12", "ref"),
            ("main", "ref"),
            ("v1.4.5", "andium"),
            ("v1.5.6", "variegata"),
            ("v2.0.0-alpha", "ref_next"),
        ]:
            with self.subTest(version=version):
                output = self.prepare(descriptor, version)
                self.assertIn(f"COMMUNITY_EXTENSION_REF={refs[field]}", output)
                self.assertIn("COMMUNITY_EXTENSION_DEPLOY=1", output)

    def test_missing_release_specific_ref_does_not_fall_back(self):
        descriptor = {
            "extension": {"name": "example"},
            "repo": {"github": "example/extension", "ref": "1" * 40},
        }
        for version in ("v1.4.5", "v1.5.6", "v2.0.0-alpha"):
            with self.subTest(version=version):
                output = self.prepare(descriptor, version)
                self.assertFalse(any(line.startswith("COMMUNITY_EXTENSION_REF=") for line in output))

    def test_sirius_release_preparation(self):
        for name in ("sirius_cuda12", "sirius_cuda13"):
            with self.subTest(extension=name):
                descriptor = yaml.safe_load((ROOT / "extensions" / name / "description.yml").read_text())
                output = self.prepare(descriptor, "v100.10.12")
                self.assertIn(f"COMMUNITY_EXTENSION_REF={descriptor['repo']['ref']}", output)
                self.assertIn("COMMUNITY_EXTENSION_BUILD_DIRECTORY=sirius-duckdb", output)
                self.assertIn(f"COMMUNITY_EXTENSION_CUDA_VERSION={descriptor['extension']['cuda_version']}", output)
                self.assertIn("COMMUNITY_EXTENSION_DEPLOY=1", output)

    def test_workflow_forwards_release_identity_without_changing_defaults(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/build.yml").read_text())
        self.assertEqual(workflow["jobs"]["prepare"]["env"]["DUCKDB_LATEST_STABLE"], "v2.0.0")
        for job in ("build", "deploy"):
            with self.subTest(job=job):
                inputs = workflow["jobs"][job]["with"]
                self.assertEqual(
                    inputs["duckdb_tag"],
                    "${{ inputs.duckdb_tag || (inputs.duckdb_commit != '' && inputs.duckdb_version || '') }}",
                )
                self.assertEqual(inputs["duckdb_version"], "${{ inputs.duckdb_version || 'v2.0.0' }}")
                self.assertIn("inputs.duckdb_commit", inputs["duckdb_commit"])
        batch = yaml.safe_load((ROOT / ".github/workflows/build_all.yml").read_text())
        for field in ("duckdb_version", "duckdb_commit", "duckdb_tag"):
            self.assertEqual(batch["jobs"]["build_all"]["with"][field], "${{ inputs." + field + " }}")


if __name__ == "__main__":
    unittest.main()
