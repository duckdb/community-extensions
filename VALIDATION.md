# Contributing Extension Validation Guide

When adding or modifying a DuckDB community extension, your `description.yml` file must pass validation.

## Quick Start

Before submitting a PR:

```bash
# Install CUE (one-time setup)
# macOS:
brew install cue

# Linux:
curl -fsSL https://cuelang.org/install.sh | sh

# Validate your changes
./scripts/validate_descriptions.sh
```

## What Gets Validated?

All `extensions/*/description.yml` files are checked for:
- Required fields (name, description, language, build, maintainers)
- Correct data types and formats
- Valid GitHub repository references
- Proper structure and syntax

## Common Issues

| Error | Solution |
|-------|----------|
| Missing required field | Add the field (e.g., `license: MIT`) |
| Invalid GitHub format | Use `owner/repo` format in `repo.github` |
| Wrong build system | Use `cmake`, `CMake`, or `cargo` |
| Invalid version type | Quote string versions: `version: "1.0.0"` |

## Full Documentation

See [schema/README.md](schema/README.md) for:
- Complete schema reference
- Field-by-field documentation
- Example files
- Troubleshooting guide

## CI Validation

Your PR will automatically run validation. Fix any errors before the PR can be merged.

**Need help?** Check the [validation documentation](schema/README.md) or ask in your PR.
