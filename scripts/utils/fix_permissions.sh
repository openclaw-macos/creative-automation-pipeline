#!/bin/bash
# Fix script permissions for Creative Automation Pipeline

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Fixing script permissions ==="
echo ""

# Make all shell scripts executable
echo "Making shell scripts executable..."
chmod +x *.sh 2>/dev/null || true
chmod +x src/*.sh 2>/dev/null || true

# Make Python scripts executable
echo "Making Python scripts executable..."
find . -name "*.py" -type f -exec chmod +x {} \; 2>/dev/null || true

# List all executable scripts
echo ""
echo "Executable scripts:"
find . -type f -name "*.sh" -executable | sort
find . -type f -name "*.py" -executable | sort

echo ""
echo "✅ Permissions fixed!"
echo ""
echo "To test localization:"
echo "  ./scripts/tests/test_localization_demo.sh"
echo ""
echo "To test video pipeline:"
echo "  ./run_video_demo.sh --target-region \"Japan\""
echo ""
echo "To test Google Drive upload:"
echo "  ./run_video_demo.sh --target-region \"USA\" --upload-to-drive"