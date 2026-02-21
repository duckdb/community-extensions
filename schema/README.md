# Extension Description Validation

This repository uses [CUE](https://cuelang.org/) to validate all `description.yml` files for community extensions. This ensures consistency, catches errors early, and maintains high quality across all extension definitions.

## What is Validated?

The validation checks:
- **Required fields**: name, description, language, build, maintainers, repo information
- **Field types**: strings, numbers, lists are properly formatted
- **GitHub repository format**: valid owner/repo structure
- **Git references**: commit hashes or valid tags
- **Build system**: valid build types (cmake, CMake, cargo)
- **Consistent structure**: all extensions follow the same schema

## Schema Definition

The schema is defined in [`schema/description.cue`](../schema/description.cue) using CUE language. It specifies:

### Required Top-Level Sections
- `extension`: Extension metadata
- `repo`: Repository information
- `docs` (optional): Documentation

### Extension Fields

**Required:**
- `name`: Extension name (non-empty string)
- `description`: Brief description (non-empty string)
- `language`: Programming language (e.g., "C++", "Rust")
- `build`: Build system ("cmake", "CMake", or "cargo")
- `maintainers`: List of maintainer GitHub usernames

**Optional:**
- `version`: Version string or number
- `license`: License identifier (e.g., "MIT", "Apache-2.0")
- `excluded_platforms`: Platforms to exclude (string or list)
- `requires_toolchains`: Required toolchains (string or list)
- `vcpkg_commit`: Specific vcpkg commit hash
- And more (see schema file for complete list)

### Repository Fields

**Required:**
- `github`: Repository in "owner/repo" format
- `ref`: Git commit hash or tag

**Optional:**
- `ref_next`: Next reference for testing
- `canonical_name`: Override canonical name

### Documentation Fields

**Optional:**
- `hello_world`: Quick start example
- `extended_description`: Detailed documentation
- `docs_url`: External documentation URL

## Validating Locally

### Prerequisites

Install CUE on your system:

**macOS:**
```bash
brew install cue
```

**Linux:**
```bash
curl -fsSL https://cuelang.org/install.sh | sh
```

**From source:**
```bash
go install cuelang.org/go/cmd/cue@latest
```

### Run Validation

From the repository root:

```bash
./scripts/validate_descriptions.sh
```

This will validate all 153 `description.yml` files and report any errors.

### Validate a Single File

```bash
cue vet schema/description.cue extensions/YOUR_EXTENSION/description.yml -d "#Description"
```

## CI/CD Integration

Validation runs automatically on:
- **Pull Requests** that modify any `description.yml` file
- **Pushes** to the main branch
- **Manual trigger** via workflow_dispatch

The workflow is defined in [`.github/workflows/validate_descriptions.yml`](../.github/workflows/validate_descriptions.yml).

### Status Checks

Pull requests must pass validation before merging. If validation fails:
1. Review the error messages in the CI logs
2. Fix the reported issues in your `description.yml`
3. Push the changes to re-run validation

## Common Validation Errors

### Missing Required Field
```
extension.license: incomplete value string
```
**Fix:** Add the missing field to your `description.yml`

### Invalid GitHub Format
```
repo.github: invalid value "invalid-format" (does not match ^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$)
```
**Fix:** Use format "owner/repository-name"

### Wrong Type
```
extension.version: conflicting values "1.0.0" and number
```
**Fix:** Version can be either string or number, but YAML interpretation matters. Quote strings: `version: "1.0.0"`

### Invalid Build System
```
extension.build: conflicting values "cmake" and "make"
```
**Fix:** Use one of the allowed values: "cmake", "CMake", or "cargo"

## Example Valid description.yml

```yaml
extension:
  name: example
  description: An example DuckDB extension
  version: "1.0.0"
  language: C++
  build: cmake
  license: MIT
  maintainers:
    - your-github-username

repo:
  github: your-org/your-extension
  ref: abc123def456... # 40-character commit hash

docs:
  hello_world: |
    SELECT example_function();
  extended_description: |
    Detailed documentation about your extension.
    Can be multiple lines.
```

## Contributing

When adding or modifying extensions:

1. Ensure your `description.yml` follows the schema
2. Run validation locally before pushing
3. Address any validation errors before submitting PR
4. CI will automatically validate your changes

## Schema Updates

If you need to add new fields to the schema:

1. Update `schema/description.cue` with the new field definition
2. Update this documentation
3. Test against all existing extensions
4. Submit PR with schema changes and documentation

## Resources

- [CUE Language Documentation](https://cuelang.org/docs/)
- [CUE Tutorials](https://cuelang.org/docs/tutorials/)
- [Schema Definition](../schema/description.cue)
- [Validation Script](../scripts/validate_descriptions.sh)
