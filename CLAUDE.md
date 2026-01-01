# Git Reference Verification

## Verifying Extension References

When working with extension `description.yml` files, **ALWAYS verify that the `repo.ref` actually exists in the remote repository**.

### How to Verify Git Refs

Use bash script (works on MacOS & Ubuntu without installing anything):

```bash
#!/usr/bin/env bash

# Parse description.yml
github_repo=$(grep "^  github:" description.yml | sed 's/.*: *//')
ref=$(grep "^  ref:" description.yml | sed 's/.*: *//')

# Verify ref exists using GitHub API
http_code=$(curl -s -o /dev/null -w "%{http_code}" \
  "https://api.github.com/repos/${github_repo}/commits/${ref}")

if [ "$http_code" = "200" ]; then
  echo "✓ Ref ${ref:0:8} exists in ${github_repo}"
else
  echo "✗ ERROR: Ref ${ref} does not exist in ${github_repo} (HTTP ${http_code})"
  exit 1
fi
```

### When to Verify

- **ALWAYS** before updating a `ref` field in description.yml
- When adding new extensions
- When user asks to verify extension integrity
- In git hooks to prevent invalid refs from being committed

### Common Ref Types

- **Commit SHA** (recommended): `723c35d44a07ee73f70e5b07b06ce5aa5dda5bc3`
- **Tag**: `v1.0.0`
- **Branch**: `main` (not recommended - use commit SHA for stability)

### Verification Script for All Extensions

Save as `scripts/verify_refs.sh`:

```bash
#!/usr/bin/env bash

set -e

failures=()

for ext_dir in extensions/*/; do
  ext_name=$(basename "$ext_dir")
  desc_file="${ext_dir}description.yml"

  [ -f "$desc_file" ] || continue

  # Extract github repo and ref
  github_repo=$(grep "^  github:" "$desc_file" 2>/dev/null | sed 's/.*: *//' || echo "")
  ref=$(grep "^  ref:" "$desc_file" 2>/dev/null | sed 's/.*: *//' || echo "")

  # Skip if no repo/ref
  [ -z "$github_repo" ] && continue
  [ -z "$ref" ] && continue

  # Verify ref exists
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://api.github.com/repos/${github_repo}/commits/${ref}")

  if [ "$http_code" = "200" ]; then
    echo "✓ ${ext_name}: ${ref:0:8} exists"
  else
    echo "✗ ${ext_name}: ref ${ref} NOT FOUND in ${github_repo} (HTTP ${http_code})"
    failures+=("$ext_name")
  fi
done

if [ ${#failures[@]} -gt 0 ]; then
  echo ""
  echo "${#failures[@]} extensions have invalid refs:"
  printf '  - %s\n' "${failures[@]}"
  exit 1
else
  echo ""
  echo "✓ All refs verified successfully"
fi
```

Make executable and run:
```bash
chmod +x scripts/verify_refs.sh
./scripts/verify_refs.sh
```

### Installing Git Pre-Commit Hook

**IMPORTANT: When user asks to enable/install/setup the pre-commit hook for ref verification:**

The hook script already exists at `scripts/pre-commit-verify-refs.sh`. To install it:

**Option 1: Symlink (recommended):**
```bash
ln -sf ../../scripts/pre-commit-verify-refs.sh .git/hooks/pre-commit
```

**Option 2: Copy:**
```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/usr/bin/env bash
exec scripts/pre-commit-verify-refs.sh
EOF
chmod +x .git/hooks/pre-commit
```

**To verify it's working:**
```bash
# Test the hook manually
.git/hooks/pre-commit

# Or make a test commit
git commit --allow-empty -m "test hook"
```

## Requirements

None! Uses only built-in tools:
- `bash` - Available on MacOS & Ubuntu
- `curl` - Pre-installed on both
- `grep`, `sed` - Standard utilities
