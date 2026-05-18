#!/usr/bin/env python3
"""
Generate extensions.json from the markdown files in build/docs/.
Run after generate_md.sh has produced the per-extension .md files.

Usage: python3 scripts/generate_extensions_json.py [build/docs] [output.json]
"""

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

SKIP_FILES = {"extensions_list.md.tmp"}


def parse_markdown_table(lines):
    """Parse a markdown pipe table into a list of dicts."""
    headers = None
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            break
        # Skip separator rows like |---|---|
        if re.match(r"^\|[-| :]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if headers is None:
            headers = cells
        else:
            rows.append(dict(zip(headers, cells)))
    return rows


def extract_tables(body):
    """Walk the markdown body and extract functions/settings/types tables."""
    functions = []
    settings = []
    types = []

    section_map = {
        "### Added Functions": functions,
        "### Overloaded Functions": functions,
        "### Added Settings": settings,
        "### Added Types": types,
    }

    lines = body.splitlines()
    i = 0
    current_target = None

    while i < len(lines):
        line = lines[i]

        # Check for a known section header
        matched = False
        for header, target in section_map.items():
            if line.strip().startswith(header):
                current_target = target
                matched = True
                break

        if not matched and line.strip().startswith("|") and current_target is not None:
            # Collect contiguous table lines
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            current_target.extend(parse_markdown_table(table_lines))
            continue

        i += 1

    return functions, settings, types


def parse_md(path):
    content = path.read_text(encoding="utf-8")

    # Front matter is between the first and second '---'
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        return None

    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        print(f"  YAML error in {path.name}: {e}", file=sys.stderr)
        return None

    if not isinstance(meta, dict):
        return None

    body = parts[2]
    functions, settings, types = extract_tables(body)

    ext = meta.get("extension") or {}
    repo = meta.get("repo") or {}
    docs = meta.get("docs") or {}
    if not isinstance(docs, dict):
        docs = {}

    record = {
        "name": ext.get("name"),
        "description": ext.get("description"),
        "version": str(ext.get("version")) if ext.get("version") is not None else None,
        "language": ext.get("language"),
        "build": ext.get("build"),
        "license": ext.get("license"),
        "maintainers": ext.get("maintainers") or [],
        "excluded_platforms": ext.get("excluded_platforms"),
        "repo": {
            k: v
            for k, v in {
                "github": repo.get("github"),
                "ref": repo.get("ref"),
            }.items()
            if v is not None
        },
        "docs": {
            k: v
            for k, v in {
                "hello_world": docs.get("hello_world"),
                "extended_description": docs.get("extended_description"),
            }.items()
            if v is not None
        },
        "star_count": meta.get("extension_star_count"),
        "download_count_last_week": meta.get("extension_download_count"),
    }

    if functions:
        record["functions"] = functions
    if settings:
        record["settings"] = settings
    if types:
        record["types"] = types

    return record


def main():
    docs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/docs")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else docs_dir / "extensions.json"

    if not docs_dir.is_dir():
        sys.exit(f"Directory not found: {docs_dir}")

    extensions = []
    for md_file in sorted(docs_dir.glob("*.md")):
        if md_file.name in SKIP_FILES:
            continue
        record = parse_md(md_file)
        if record and record.get("name"):
            extensions.append(record)
        else:
            print(f"  Skipped {md_file.name}", file=sys.stderr)

    output_path.write_text(json.dumps(extensions, indent=2, ensure_ascii=False))
    print(f"Generated {output_path} with {len(extensions)} extensions")


if __name__ == "__main__":
    main()
