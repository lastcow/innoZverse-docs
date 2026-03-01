#!/bin/bash
# Extract bash code blocks from lab files and run them
# Generates SVG terminal screenshots via script capture

set -euo pipefail

RESULTS_DIR="lab-results"
PASS=0
FAIL=0
SKIP=0

mkdir -p "$RESULTS_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

run_lab() {
    local lab_file="$1"
    local lab_name=$(basename "$lab_file" .md)
    local section=$(echo "$lab_file" | cut -d'/' -f1)
    local level=$(echo "$lab_file" | cut -d'/' -f2)
    local result_dir="$RESULTS_DIR/$section/$level"
    
    mkdir -p "$result_dir"
    
    echo -e "${YELLOW}Running: $lab_file${NC}"
    
    # Extract bash code blocks (skip blocks with # SKIP or sudo/reboot/shutdown)
    python3 scripts/extract_code_blocks.py "$lab_file" > "/tmp/lab_commands.sh" 2>/dev/null || {
        echo -e "${YELLOW}  SKIP: No runnable commands${NC}"
        ((SKIP++)) || true
        return
    }
    
    if [ ! -s "/tmp/lab_commands.sh" ]; then
        ((SKIP++)) || true
        return
    fi
    
    # Run commands and capture output
    local output_file="$result_dir/${lab_name}.txt"
    local svg_file="$result_dir/${lab_name}.svg"
    
    if timeout 60 bash /tmp/lab_commands.sh > "$output_file" 2>&1; then
        echo -e "${GREEN}  ✅ PASS${NC}"
        ((PASS++)) || true
        
        # Generate SVG using ansifilter + carbon or aha
        if command -v aha &>/dev/null; then
            cat "$output_file" | aha --title "$lab_name" > "$result_dir/${lab_name}.html"
        fi
        
        echo "PASS" > "$result_dir/${lab_name}.status"
    else
        echo -e "${RED}  ❌ FAIL${NC}"
        cat "$output_file"
        ((FAIL++)) || true
        echo "FAIL" > "$result_dir/${lab_name}.status"
    fi
}

# Find all lab files
find linux -path "*/labs/lab-*.md" | sort | while read lab; do
    run_lab "$lab"
done

echo ""
echo "================================"
echo "Results: ✅ $PASS passed | ❌ $FAIL failed | ⏭️ $SKIP skipped"
echo "================================"

# Write summary
cat > "$RESULTS_DIR/summary.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "passed": $PASS,
  "failed": $FAIL,
  "skipped": $SKIP,
  "total": $((PASS + FAIL + SKIP))
}
EOF

[ $FAIL -eq 0 ]
