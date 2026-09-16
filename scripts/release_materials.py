"""Publish verified native release materials around DuckDB's existing uploader.

The extension provides release/SHA256SUMS and distribution-manifest.json with
extension_sha256. This helper is maintained in the workflow repository; it never
executes code from the build artifact. Source completeness is the extension
maintainer's responsibility. Checksums establish which materials accompany a
particular binary, not whether those materials satisfy a license.
"""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile


SIGNATURE_BYTES = 256
CHUNK_SIZE = 1024 * 1024
PUBLIC_BASE = "https://community-extensions.duckdb.org"


def digest(path, limit=None):
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        while limit is None or limit > 0:
            chunk = source.read(CHUNK_SIZE if limit is None else min(CHUNK_SIZE, limit))
            if not chunk:
                if limit:
                    raise ValueError(f"Truncated file: {path.name}")
                break
            checksum.update(chunk)
            if limit is not None:
                limit -= len(chunk)
    return checksum.hexdigest()


def segment(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", value):
        raise ValueError(f"Invalid deployment identifier: {value!r}")
    return value


def regular_file(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"Expected a regular file: {path.name}")
    return path


def verify_materials(artifact, name):
    binary = regular_file(artifact / f"{segment(name)}.duckdb_extension")
    if binary.stat().st_size <= SIGNATURE_BYTES:
        raise ValueError("Extension is too short to contain a signature trailer")
    release = artifact / "release"
    if release.is_symlink() or not release.is_dir():
        raise ValueError("Missing release directory, or release is a symlink")
    checksums = regular_file(release / "SHA256SUMS")
    files = {}
    for line in checksums.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64}) [ *]([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if not match:
            raise ValueError("SHA256SUMS must contain hashes and flat, relative filenames")
        expected, filename = match.groups()
        if filename in files or filename == "SHA256SUMS":
            raise ValueError(f"Duplicate or recursive checksum: {filename}")
        path = regular_file(release / filename)
        if digest(path) != expected.lower():
            raise ValueError(f"Checksum mismatch: {filename}")
        files[filename] = expected.lower()
    if "distribution-manifest.json" not in files:
        raise ValueError("distribution-manifest.json must be covered by SHA256SUMS")
    if set(p.name for p in release.iterdir()) != set(files) | {"SHA256SUMS"}:
        raise ValueError("Every release file must be covered by SHA256SUMS")
    manifest = json.loads((release / "distribution-manifest.json").read_text(encoding="utf-8"))
    unsigned_hash = digest(binary)
    if manifest.get("extension_sha256") != unsigned_hash:
        raise ValueError("Release manifest does not match the unsigned extension")
    files["SHA256SUMS"] = digest(checksums)
    return binary, files, unsigned_hash


def verify_signed_download(unsigned, downloaded):
    """Only the last 256 signature bytes may differ after native publication."""
    signed_hash = hashlib.sha256()
    remaining = unsigned.stat().st_size - SIGNATURE_BYTES
    with unsigned.open("rb") as original, gzip.open(downloaded, "rb") as signed:
        while remaining:
            expected = original.read(min(CHUNK_SIZE, remaining))
            actual = signed.read(len(expected))
            if not expected or actual != expected:
                raise ValueError("Published extension payload differs from the source-associated build")
            signed_hash.update(actual)
            remaining -= len(expected)
        signature = signed.read(SIGNATURE_BYTES)
        if len(signature) != SIGNATURE_BYTES or not any(signature) or signed.read(1):
            raise ValueError("Published extension has an invalid signature trailer or length")
        signed_hash.update(signature)
    return signed_hash.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def upload(path, bucket, key):
    subprocess.run(["aws", "s3", "cp", str(path), f"s3://{bucket}/{key}", "--acl", "public-read"], check=True)


def publish(args):
    for value in (args.name, args.extension_version, args.duckdb_version, args.arch, args.bucket):
        segment(value)
    if args.arch.startswith("wasm"):
        raise ValueError("Release-material publication currently supports native extensions only")
    if not args.deploy_latest and not args.deploy_versioned:
        raise ValueError("At least one binary deployment destination must be enabled")
    artifact = args.artifact_dir.resolve()
    binary, files, unsigned_hash = verify_materials(artifact, args.name)
    prefix = (
        f"release_materials/{args.name}/{args.extension_version}/{args.duckdb_version}/{args.arch}/"
        f"{unsigned_hash}/{files['SHA256SUMS']}"
    )
    filename = f"{args.name}.duckdb_extension.gz"
    destinations = []
    if args.deploy_versioned:
        destinations.append(f"{args.name}/{args.extension_version}/{args.duckdb_version}/{args.arch}/{filename}")
    if args.deploy_latest:
        destinations.append(f"{args.duckdb_version}/{args.arch}/{filename}")
    source_index = {
        "schema_version": 1,
        "extension": args.name,
        "extension_version": args.extension_version,
        "duckdb_version": args.duckdb_version,
        "platform": args.arch,
        "unsigned_extension_sha256": unsigned_hash,
        "payload_sha256": digest(binary, binary.stat().st_size - SIGNATURE_BYTES),
        "files": {
            name: {"sha256": checksum, "url": f"{PUBLIC_BASE}/{prefix}/files/{name}"}
            for name, checksum in sorted(files.items())
        },
    }
    if not args.publish:
        print(json.dumps({"source_index": source_index, "binary_destinations": destinations}, indent=2))
        print("Validation passed; no uploads or signing performed. Use --publish in the deployment workflow.")
        return
    if os.environ.get("DUCKDB_DEPLOY_SCRIPT_MODE") != "for_real":
        raise ValueError("--publish requires DUCKDB_DEPLOY_SCRIPT_MODE=for_real")
    if not os.environ.get("AWS_ACCESS_KEY_ID"):
        raise ValueError("Publishing requires AWS credentials")
    if not os.environ.get("DUCKDB_EXTENSION_SIGNING_PK"):
        raise ValueError("Publishing requires the community extension signing key")
    deploy_script = args.deploy_script.resolve()
    regular_file(deploy_script)

    with tempfile.TemporaryDirectory(prefix="duckdb-release-materials-") as tmp:
        tmp = Path(tmp)
        # Finish every source upload before allowing the existing binary uploader
        # to run. Material locations are keyed by both binary and material hashes.
        for name in sorted(files):
            upload(artifact / "release" / name, args.bucket, f"{prefix}/files/{name}")
        index_path = tmp / "source-index.json"
        write_json(index_path, source_index)
        upload(index_path, args.bucket, f"{prefix}/source-index.json")

        subprocess.run(
            [
                str(deploy_script),
                args.name,
                args.extension_version,
                args.duckdb_version,
                args.arch,
                args.bucket,
                str(args.deploy_latest).lower(),
                str(args.deploy_versioned).lower(),
                str(artifact),
            ],
            check=True,
        )
        # The DuckDB uploader signs/compresses a copy. Ensure its original input
        # and accompanying materials stayed intact before recording publication.
        if verify_materials(artifact, args.name) != (binary, files, unsigned_hash):
            raise ValueError("Release materials changed during deployment")
        for key in destinations:
            downloaded = tmp / "published.duckdb_extension.gz"
            subprocess.run(["aws", "s3", "cp", f"s3://{args.bucket}/{key}", str(downloaded)], check=True)
            signed_hash = verify_signed_download(binary, downloaded)
            receipt = {
                **source_index,
                "binary_url": f"{PUBLIC_BASE}/{key}",
                "download_sha256": digest(downloaded),
                "signed_extension_sha256": signed_hash,
                "source_index_url": f"{PUBLIC_BASE}/{prefix}/source-index.json",
            }
            receipt_path = tmp / "publication.json"
            write_json(receipt_path, receipt)
            receipt_key = f"{prefix}/publication-{digest(receipt_path)}.json"
            upload(receipt_path, args.bucket, receipt_key)
            # Existing cache invalidation for <name>.duckdb_extension.* also
            # covers this discoverable receipt beside each binary download.
            upload(receipt_path, args.bucket, key[:-3] + ".sources.json")
            print(f"Published source association: {PUBLIC_BASE}/{receipt_key}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=Path("/tmp/extension"))
    parser.add_argument("--deploy-script", type=Path, default=Path("duckdb/scripts/extension-upload-single.sh"))
    for flag in ("name", "extension-version", "duckdb-version", "arch", "bucket"):
        parser.add_argument("--" + flag, required=True)
    parser.add_argument("--deploy-latest", choices=("true", "false"), default="false")
    parser.add_argument("--deploy-versioned", choices=("true", "false"), default="false")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    args.deploy_latest = args.deploy_latest == "true"
    args.deploy_versioned = args.deploy_versioned == "true"
    publish(args)


if __name__ == "__main__":
    main()
