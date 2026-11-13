#!/usr/bin/env python3
"""
Print a markdown compatibility matrix (DuckDB version x platform) for a community extension.

A cell is marked as supported if the extension binary exists in the community repository,
and as unsupported if requesting it returns a 404. Any other outcome (e.g. rate limiting by
the CDN) is retried, and shown as unknown if it keeps failing, rather than reported as unsupported.

Usage: python3 scripts/compatibility_matrix.py extension_name duckdb_releases.csv
       python3 scripts/compatibility_matrix.py --versions duckdb_releases.csv

  duckdb_releases.csv: https://raw.githubusercontent.com/duckdb/duckdb-web/main/_data/past_releases.csv

With --versions, only the DuckDB versions shown in the matrix are printed, newest first, one per line.
"""

import csv
import datetime
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

REPOSITORY = "https://community-extensions.duckdb.org"
# Number of most recent patch releases to show for each supported minor version
PATCHES_PER_CYCLE = 2
# A full docs run (~13k requests at this concurrency) was not throttled by the CDN
MAX_PARALLEL_REQUESTS = 16
# Requests that fail with anything other than a 404 are retried with exponential backoff
RETRIES = 4

# Platforms shown in the matrix, in display order
PLATFORMS = {
    "linux_amd64": "Linux AMD64",
    "linux_arm64": "Linux ARM64",
    "osx_amd64": "macOS AMD64",
    "osx_arm64": "macOS ARM64",
    "windows_amd64": "Windows AMD64",
    "windows_arm64": "Windows ARM64",
    "wasm_eh": "WebAssembly",
}


def version_key(version):
    return tuple(int(part) for part in version.split("."))


def supported_versions(releases_path):
    """Return the most recent patch releases of all DuckDB versions that have not reached end-of-life."""
    with open(releases_path) as f:
        releases = list(csv.DictReader(f))
    # Patch releases per minor version, e.g. (1, 5) -> ["1.5.6", "1.5.5", ...]
    cycles = {}
    for release in releases:
        cycles.setdefault(version_key(release["version_number"])[:2], []).append(release["version_number"])
    # The end-of-life date of a minor version is set on its x.y.0 release
    end_of_life = {version_key(r["version_number"])[:2]: r["end_of_life"] for r in releases if r["version_number"].endswith(".0")}
    newest = max(cycles)
    today = datetime.date.today().isoformat()
    versions = []
    for cycle, patches in cycles.items():
        # The newest minor version may not have an end-of-life date yet
        if cycle == newest or end_of_life.get(cycle, "") > today:
            versions += sorted(patches, key=version_key)[-PATCHES_PER_CYCLE:]
    return sorted(versions, key=version_key)


def is_available(extension, version, platform):
    """Return True if the binary exists, False on a 404, and None if it could not be determined."""
    suffix = "wasm" if platform.startswith("wasm") else "gz"
    url = f"{REPOSITORY}/v{version}/{platform}/{extension}.duckdb_extension.{suffix}"
    # The CDN rejects urllib's default User-Agent with a 403
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "duckdb-community-extensions-docs"})
    for attempt in range(RETRIES):
        if attempt > 0:
            time.sleep(2**attempt)
        try:
            with urllib.request.urlopen(request, timeout=30):
                return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            error = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError) as e:
            error = str(getattr(e, "reason", e))
    print(f"Could not determine availability of {url}: {error}", file=sys.stderr)
    return None


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    extension, releases_path = sys.argv[1:]

    versions = supported_versions(releases_path)
    if extension == "--versions":
        print("\n".join(reversed(versions)))
        return
    cells = [(platform, version) for platform in PLATFORMS for version in versions]
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_REQUESTS) as pool:
        results = pool.map(lambda c: is_available(extension, c[1], c[0]), cells)
    available = dict(zip(cells, results))

    recent = "most recent patch release" if PATCHES_PER_CYCLE == 1 else f"{PATCHES_PER_CYCLE} most recent patch releases"
    print(
        "This table covers all DuckDB releases that have not reached "
        "[end-of-life](https://duckdb.org/release_calendar), including LTS releases, "
        f"and shows the {recent} of each. "
        "Older patch releases are not listed, but the extension may be available for them as well."
    )
    print()
    # Placed directly before the table, like the markers of the other tables on the page
    print('<div class="extension_compatibility_table"></div>')
    print()
    print("| Platform | " + " | ".join(versions) + " |")
    print("| :--- | " + " | ".join(":---:" for _ in versions) + " |")
    for platform, name in PLATFORMS.items():
        marks = [{True: "✅", False: "❌", None: "❓"}[available[(platform, version)]] for version in versions]
        print(f"| {name} | " + " | ".join(marks) + " |")


if __name__ == "__main__":
    main()
