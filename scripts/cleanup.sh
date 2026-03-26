#!/bin/bash
# Cleanup and organize outputs for Creative Automation Pipeline
# Moves test files to test_outputs/, backups to backups/
# Optional: clean old campaign directories

set -e
set -u  # Treat unset variables as errors

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧹 Cleanup & Organize Outputs"
echo "=============================="
echo ""

# Create necessary directories
mkdir -p "$PROJECT_ROOT/test_outputs"
mkdir -p "$PROJECT_ROOT/backups"
mkdir -p "$PROJECT_ROOT/test_reports"

echo "📁 Created directories:"
echo "  - test_outputs/"
echo "  - backups/"
echo "  - test_reports/"
echo ""

# Move test output files
echo "Moving test output files to test_outputs/..."
for file in "$PROJECT_ROOT"/*.txt "$PROJECT_ROOT"/*.log "$PROJECT_ROOT"/outputs/*.txt 2>/dev/null; do
    if [ -f "$file" ]; then
        mv "$file" "$PROJECT_ROOT/test_outputs/"
        echo "  📄 Moved: $(basename "$file")"
    fi
done

# Move backup files to backups/
echo "Moving backup files to backups/..."
for file in "$PROJECT_ROOT"/*.backup* "$PROJECT_ROOT"/*.bak "$PROJECT_ROOT"/run_*.sh.backup*; do
    if [ -f "$file" ]; then
        mv "$file" "$PROJECT_ROOT/backups/"
        echo "  💾 Moved: $(basename "$file")"
    fi
done

# Move test reports if any
if [ -d "$PROJECT_ROOT/outputs/logs" ]; then
    for file in "$PROJECT_ROOT/outputs/logs"/*.json "$PROJECT_ROOT/outputs/logs"/*.db 2>/dev/null; do
        if [ -f "$file" ]; then
            cp "$file" "$PROJECT_ROOT/test_outputs/"
            echo "  📊 Copied test data: $(basename "$file")"
        fi
    done
fi

echo ""
echo "✅ Output organization complete"
echo ""

# Optional: Clean old campaign directories (commented out by default)
# Uncomment lines below to enable automatic cleaning of old campaign directories
# echo "💡 Optional: To clean old campaign directories automatically, uncomment the"
# echo " optional section in scripts/cleanup.sh (lines 170-185)."
# echo ""
# # Optional section start (line ~170)
# # echo "Cleaning old campaign directories (older than 7 days)..."
# # for dir in "$PROJECT_ROOT"/campaign_* "$PROJECT_ROOT"/outputs/campaign_* 2>/dev/null; do
# #     if [ -d "$dir" ]; then
# #         dir_age=$(( $(date +%s) - $(stat -f %m "$dir") ))
# #         if [ $dir_age -gt 604800 ]; then  # 7 days in seconds
# #             echo "  🗑️  Removing old: $(basename "$dir")"
# #             rm -rf "$dir"
# #         fi
# #     fi
# # done
# # cd - >/dev/null
# # } || true
# # Optional section end

echo ""
echo "🎯 Tip: Add './scripts/cleanup.sh' to your .gitignore if you want to keep"
echo " temporary files out of version control."
echo ""
echo "💡 To clean old campaign directories automatically, uncomment the"
echo " optional section in scripts/cleanup.sh (lines 170-185)."