#!/usr/bin/env bash

# Only check modified description.yml files
changed_files=$(git diff --cached --name-only --diff-filter=ACM | grep "description.yml$" || true)

[ -z "$changed_files" ] && exit 0

echo "Verifying git refs in modified description.yml files..."

failures=()

for desc_file in $changed_files; do
  ext_name=$(dirname "$desc_file" | xargs basename)

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
    echo "✓ ${ext_name}: ${ref:0:8} verified"
  else
    echo "✗ ${ext_name}: ref ${ref} NOT FOUND in ${github_repo}"
    failures+=("$ext_name")
  fi
done

if [ ${#failures[@]} -gt 0 ]; then
  echo ""
  echo "ERROR: ${#failures[@]} extensions have invalid refs. Commit rejected."
  exit 1
fi

echo "✓ All refs verified"
