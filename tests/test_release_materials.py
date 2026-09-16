import contextlib
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import release_materials as materials


class ReleaseMaterialsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.artifact = self.root / 'artifact'
        self.release = self.artifact / 'release'
        self.release.mkdir(parents=True)
        self.binary = self.artifact / 'example.duckdb_extension'
        self.payload = b'extension payload\n' * 70000  # Exercise chunk boundaries.
        self.binary.write_bytes(self.payload + bytes(materials.SIGNATURE_BYTES))
        (self.release / 'source.tar.gz').write_bytes(gzip.compress(b'corresponding source fixture'))
        (self.release / 'LICENSE').write_text('License fixture\n')
        materials.write_json(
            self.release / 'distribution-manifest.json',
            {
                'extension_sha256': materials.digest(self.binary),
            },
        )
        self.write_checksums()
        self.signer = self.root / 'extension-upload-single.sh'
        self.signer.write_text('# Fixture: intercepted by fake_run\n')
        self.args = SimpleNamespace(
            artifact_dir=self.artifact,
            deploy_script=self.signer,
            name='example',
            extension_version='abc123',
            duckdb_version='v1.5.5',
            arch='linux_amd64',
            bucket='test-bucket',
            deploy_latest=True,
            deploy_versioned=True,
            publish=True,
        )
        self.objects = {}
        self.calls = []
        self.addCleanup(patch.stopall)
        patch.dict(
            os.environ,
            {
                'DUCKDB_DEPLOY_SCRIPT_MODE': 'for_real',
                'AWS_ACCESS_KEY_ID': 'test-only',
                'DUCKDB_EXTENSION_SIGNING_PK': 'test-only',
            },
        ).start()
        self.run_patch = patch.object(materials.subprocess, 'run', side_effect=self.fake_run)
        self.run = self.run_patch.start()

    def write_checksums(self):
        entries = sorted(p for p in self.release.iterdir() if p.name != 'SHA256SUMS')
        (self.release / 'SHA256SUMS').write_text(
            ''.join(f'{materials.digest(path)}  {path.name}\n' for path in entries)
        )

    def binary_keys(self):
        filename = f'{self.args.duckdb_version}/{self.args.arch}/example.duckdb_extension.gz'
        return [f'example/{self.args.extension_version}/{filename}', filename]

    def fake_run(self, command, check):
        self.assertTrue(check)
        self.calls.append(command)
        if command[0] == str(self.signer):
            self.assertEqual(
                command[1:],
                [
                    'example',
                    self.args.extension_version,
                    'v1.5.5',
                    self.args.arch,
                    'test-bucket',
                    'true',
                    'true',
                    str(self.artifact),
                ],
            )
            # Material uploads and their index must finish before binary publication.
            indices = [key for key in self.objects if key.endswith('/source-index.json')]
            self.assertEqual(len(indices), 1)
            index = json.loads(self.objects[indices[0]])
            for entry in index['files'].values():
                key = entry['url'].removeprefix(materials.PUBLIC_BASE + '/')
                self.assertEqual(hashlib.sha256(self.objects[key]).hexdigest(), entry['sha256'])
            data = gzip.compress(self.payload + b's' * materials.SIGNATURE_BYTES)
            for key in self.binary_keys():
                self.objects[key] = data
        else:
            self.assertEqual(command[:3], ['aws', 's3', 'cp'])
            source, destination = command[3:5]
            if source.startswith('s3://'):
                Path(destination).write_bytes(self.objects[source.removeprefix('s3://test-bucket/')])
            else:
                self.assertEqual(command[5:], ['--acl', 'public-read'])
                self.objects[destination.removeprefix('s3://test-bucket/')] = Path(source).read_bytes()
        return subprocess.CompletedProcess(command, 0)

    def publish(self):
        with contextlib.redirect_stdout(io.StringIO()):
            materials.publish(self.args)

    def test_publish_associates_both_signed_downloads_with_verified_materials(self):
        self.publish()
        for key in self.binary_keys():
            receipt_bytes = self.objects[key[:-3] + '.sources.json']
            receipt = json.loads(receipt_bytes)
            self.assertEqual(receipt['binary_url'], materials.PUBLIC_BASE + '/' + key)
            self.assertEqual(receipt['download_sha256'], hashlib.sha256(self.objects[key]).hexdigest())
            self.assertEqual(
                receipt['signed_extension_sha256'], hashlib.sha256(gzip.decompress(self.objects[key])).hexdigest()
            )
            self.assertEqual(receipt['unsigned_extension_sha256'], materials.digest(self.binary))
            self.assertEqual(receipt['payload_sha256'], hashlib.sha256(self.payload).hexdigest())
            index_key = receipt['source_index_url'].removeprefix(materials.PUBLIC_BASE + '/')
            immutable = index_key.removesuffix('source-index.json') + (
                'publication-' + hashlib.sha256(receipt_bytes).hexdigest() + '.json'
            )
            self.assertEqual(self.objects[immutable], receipt_bytes)

    def test_dry_run_never_invokes_signer_or_storage(self):
        self.args.publish = False
        self.publish()
        self.run.assert_not_called()

    def test_material_filenames_cannot_overwrite_publication_metadata(self):
        (self.release / 'source-index.json').write_text('producer-supplied file')
        self.write_checksums()
        self.publish()
        for key in self.binary_keys():
            receipt = json.loads(self.objects[key[:-3] + '.sources.json'])
            source = receipt['files']['source-index.json']['url'].removeprefix(materials.PUBLIC_BASE + '/')
            self.assertEqual(self.objects[source], b'producer-supplied file')
            self.assertNotEqual(receipt['files']['source-index.json']['url'], receipt['source_index_url'])

    def test_material_failures_prevent_all_external_calls(self):
        original = (self.release / 'SHA256SUMS').read_text()
        mutations = {
            'checksum mismatch': original.replace(original[:64], '0' * 64, 1),
            'duplicate': original + original.splitlines()[0] + '\n',
            'traversal': '0' * 64 + '  ../private.pem\n',
            'absolute path': '0' * 64 + '  /private.pem\n',
            'missing manifest': '\n'.join(
                line for line in original.splitlines() if 'distribution-manifest.json' not in line
            ),
            'self reference': original + '0' * 64 + '  SHA256SUMS\n',
        }
        for reason, checksums in mutations.items():
            with self.subTest(reason=reason):
                (self.release / 'SHA256SUMS').write_text(checksums)
                with self.assertRaises(ValueError):
                    self.publish()
                self.run.assert_not_called()
        (self.release / 'SHA256SUMS').write_text(original)
        (self.release / 'untracked').write_text('not covered')
        with self.assertRaises(ValueError):
            self.publish()
        self.run.assert_not_called()

    def test_manifest_must_identify_the_actual_build_binary(self):
        self.binary.write_bytes(self.payload + b'x' * materials.SIGNATURE_BYTES)
        with self.assertRaisesRegex(ValueError, 'does not match'):
            self.publish()
        self.run.assert_not_called()

    def test_missing_materials_and_symlinks_are_rejected(self):
        license_file = self.release / 'LICENSE'
        saved = self.root / 'LICENSE'
        license_file.rename(saved)
        with self.assertRaises(FileNotFoundError):
            self.publish()
        license_file.symlink_to(saved)
        with self.assertRaisesRegex(ValueError, 'regular file'):
            self.publish()
        self.run.assert_not_called()

    def test_source_upload_failure_prevents_signing(self):
        self.run.side_effect = subprocess.CalledProcessError(1, ['aws'])
        with self.assertRaises(subprocess.CalledProcessError):
            self.publish()
        self.assertEqual(self.run.call_count, 1)
        self.assertEqual(self.run.call_args.args[0][0], 'aws')

    def test_signer_failure_does_not_create_publication_receipts(self):
        def fail_signer(command, check):
            if command[0] == str(self.signer):
                raise subprocess.CalledProcessError(1, command)
            return self.fake_run(command, check)

        self.run.side_effect = fail_signer
        with self.assertRaises(subprocess.CalledProcessError):
            self.publish()
        self.assertTrue(self.objects)
        self.assertFalse(any('publication-' in key or key.endswith('.sources.json') for key in self.objects))

    def test_changed_materials_during_deployment_prevent_receipts(self):
        def mutate(command, check):
            result = self.fake_run(command, check)
            if command[0] == str(self.signer):
                (self.release / 'LICENSE').write_text('modified')
            return result

        self.run.side_effect = mutate
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            self.publish()
        self.assertFalse(any(key.endswith('.sources.json') for key in self.objects))

    def test_download_must_preserve_payload_and_length(self):
        downloaded = self.root / 'download.gz'
        valid = self.payload + b's' * materials.SIGNATURE_BYTES
        for data in (b'X' + valid[1:], valid[:-1], valid + b'X', self.binary.read_bytes()):
            with self.subTest(length=len(data)):
                downloaded.write_bytes(gzip.compress(data))
                with self.assertRaises(ValueError):
                    materials.verify_signed_download(self.binary, downloaded)
        downloaded.write_bytes(gzip.compress(valid)[:-5])
        with self.assertRaises(EOFError):
            materials.verify_signed_download(self.binary, downloaded)

    def test_invalid_destination_and_missing_publication_guards(self):
        for name in ('../example', 'example/name', 'example\nINJECT=1'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                materials.segment(name)
        self.args.arch = 'wasm_mvp'
        with self.assertRaisesRegex(ValueError, 'native'):
            self.publish()
        self.args.arch = 'linux_amd64'
        for variable in ('DUCKDB_DEPLOY_SCRIPT_MODE', 'AWS_ACCESS_KEY_ID', 'DUCKDB_EXTENSION_SIGNING_PK'):
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: ''}):
                with self.assertRaises(ValueError):
                    self.publish()
        self.run.assert_not_called()

    @unittest.skipUnless(os.environ.get('DUCKDB_UPLOAD_SCRIPT'), 'Set DUCKDB_UPLOAD_SCRIPT for signer integration')
    def test_real_duckdb_signer_with_local_storage(self):
        # Use DuckDB's unmodified signing/compression script and a disposable key.
        # The aws executable below only copies local files; no cloud is contacted.
        self.run_patch.stop()
        self.args.deploy_script = Path(os.environ['DUCKDB_UPLOAD_SCRIPT']).resolve()
        key = self.root / 'test-key.pem'
        subprocess.run(
            ['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048', '-out', str(key)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        store = self.root / 'storage'
        executables = self.root / 'bin'
        executables.mkdir()
        aws = executables / 'aws'
        aws.write_text(
            f'#!{sys.executable}\n'
            + '''import os
from pathlib import Path
import shutil
import sys
assert sys.argv[1:3] == ['s3', 'cp']
def local(path):
    return Path(os.environ['TEST_S3_ROOT']) / path[5:] if path.startswith('s3://') else Path(path)
source, destination = map(local, sys.argv[3:5])
destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, destination)
'''
        )
        aws.chmod(0o755)
        with contextlib.chdir(self.root), patch.dict(
            os.environ,
            {
                'PATH': str(executables) + os.pathsep + os.environ['PATH'],
                'TEST_S3_ROOT': str(store),
                'DUCKDB_EXTENSION_SIGNING_PK': key.read_text(),
            },
        ):
            self.publish()
        for binary_key in self.binary_keys():
            downloaded = store / 'test-bucket' / binary_key
            receipt = json.loads(downloaded.with_suffix('.sources.json').read_text())
            signed = gzip.decompress(downloaded.read_bytes())
            self.assertNotEqual(signed[-materials.SIGNATURE_BYTES :], bytes(materials.SIGNATURE_BYTES))
            self.assertEqual(receipt['download_sha256'], materials.digest(downloaded))
            self.assertEqual(receipt['signed_extension_sha256'], hashlib.sha256(signed).hexdigest())
            self.assertEqual(signed[: -materials.SIGNATURE_BYTES], self.payload)
        self.assertEqual(self.binary.read_bytes(), self.payload + bytes(materials.SIGNATURE_BYTES))


if __name__ == '__main__':
    unittest.main()
