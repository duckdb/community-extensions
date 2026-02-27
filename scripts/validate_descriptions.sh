#!/bin/bash
# Validate all description.yml files using CUE

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SCHEMA_FILE="$REPO_ROOT/schema/description.cue"
EXTENSIONS_DIR="$REPO_ROOT/extensions"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if CUE is installed
if ! command -v cue &> /dev/null; then
    echo -e "${RED}Error: CUE is not installed${NC}"
    echo "Install CUE from: https://cuelang.org/docs/install/"
    echo ""
    echo "Quick install options:"
    echo "  macOS:   brew install cue"
    echo "  Linux:   go install cuelang.org/go/cmd/cue@latest"
    echo "  Binary:  Download from https://github.com/cue-lang/cue/releases"
    exit 1
fi

echo "Validating description.yml files with CUE..."
echo "Schema: $SCHEMA_FILE"
echo ""

FAILED_FILES=()
TOTAL_FILES=0
PASSED_FILES=0

# Find all description.yml files
while IFS= read -r file; do
    TOTAL_FILES=$((TOTAL_FILES + 1))
    EXTENSION_NAME=$(basename "$(dirname "$file")")
    
    # Validate using CUE
    if cue vet "$SCHEMA_FILE" "$file" -d "#Description" 2>&1; then
        PASSED_FILES=$((PASSED_FILES + 1))
        echo -e "${GREEN}✓${NC} $EXTENSION_NAME"
    else
        FAILED_FILES+=("$file")
        echo -e "${RED}✗${NC} $EXTENSION_NAME"
    fi
done < <(find "$EXTENSIONS_DIR" -name "description.yml" | sort)

echo ""
echo "----------------------------------------"
echo "Validation Summary:"
echo "  Total files:  $TOTAL_FILES"
echo -e "  ${GREEN}Passed:      $PASSED_FILES${NC}"
echo -e "  ${RED}Failed:      ${#FAILED_FILES[@]}${NC}"
echo "----------------------------------------"

# Exit with error if any files failed
if [ ${#FAILED_FILES[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed files:${NC}"
    for file in "${FAILED_FILES[@]}"; do
        echo "  - $file"
    done
    exit 1
else
    echo -e "\n${GREEN}All description.yml files are valid!${NC}"
    exit 0
fi
