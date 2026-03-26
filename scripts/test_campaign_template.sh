#!/bin/bash
# Template for testing campaigns with proper timestamp format
# Uses standardized timestamp format: YYYYMMDD_HHMM (no seconds)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source timestamp utilities
source "$SCRIPT_DIR/timestamp_utils.sh"

# Configuration
CAMPAIGN_NAME="$1"  # e.g., "1_Smart_Kitchen_Essentials_North_America"
BRIEF_FILE="configs/examples/${CAMPAIGN_NAME}/brief.json"

if [ -z "$CAMPAIGN_NAME" ] || [ ! -f "$BRIEF_FILE" ]; then
    echo "❌ Usage: $0 <campaign_name>"
    echo "   Example: $0 1_Smart_Kitchen_Essentials_North_America"
    echo "   Available campaigns:"
    ls -1 configs/examples/ 2>/dev/null || echo "   No campaigns found in configs/examples/"
    exit 1
fi

# Get timestamp (no seconds)
TIMESTAMP=$(get_timestamp_no_seconds)
echo "=== Testing Campaign: $CAMPAIGN_NAME ==="
echo "Timestamp: $TIMESTAMP"
echo ""

# Create test output filename with correct timestamp format
TEST_OUTPUT_FILE="${PROJECT_ROOT}/test_outputs/campaign_test_${CAMPAIGN_NAME}_${TIMESTAMP}.txt"
mkdir -p "$(dirname "$TEST_OUTPUT_FILE")"

echo "📝 Test output: $TEST_OUTPUT_FILE"
echo "📋 Campaign brief: $BRIEF_FILE"
echo ""

# Run campaign demo
echo "🚀 Running campaign demo..."
START_TIME=$(date +%s)

./run_campaign_demo.sh --brief "$BRIEF_FILE" --verbose 2>&1 | tee "$TEST_OUTPUT_FILE"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "⏱️  Campaign completed in ${DURATION} seconds"

# Rename campaign folder with correct timestamp format
if [ -d "outputs/campaign" ]; then
    NEW_FOLDER_NAME="outputs/campaign_${CAMPAIGN_NAME}_${TIMESTAMP}"
    mv "outputs/campaign" "$NEW_FOLDER_NAME"
    echo "📁 Campaign output folder: $NEW_FOLDER_NAME"
else
    echo "⚠️  No outputs/campaign folder found"
fi

# Generate test report
REPORT_FILENAME=$(get_test_report_filename "test_report_${CAMPAIGN_NAME}")
REPORT_FILE="${PROJECT_ROOT}/test_reports/${REPORT_FILENAME}"

echo "📊 Generating test report: $REPORT_FILE"
echo "# Test Report: $CAMPAIGN_NAME" > "$REPORT_FILE"
echo "## Test Details" >> "$REPORT_FILE"
echo "- **Date:** $(get_readable_date)" >> "$REPORT_FILE"
echo "- **Campaign:** $CAMPAIGN_NAME" >> "$REPORT_FILE"
echo "- **Duration:** ${DURATION} seconds" >> "$REPORT_FILE"
echo "- **Output Folder:** campaign_${CAMPAIGN_NAME}_${TIMESTAMP}" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## Commands Executed" >> "$REPORT_FILE"
echo "1. \`./run_campaign_demo.sh --brief \"$BRIEF_FILE\" --verbose\`" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## Test Output" >> "$REPORT_FILE"
echo '```bash' >> "$REPORT_FILE"
tail -20 "$TEST_OUTPUT_FILE" >> "$REPORT_FILE" 2>/dev/null || echo "No test output available" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"

echo ""
echo "✅ Test completed successfully!"
echo "   Output folder: campaign_${CAMPAIGN_NAME}_${TIMESTAMP}"
echo "   Test report: $REPORT_FILE"
echo "   Raw output: $TEST_OUTPUT_FILE"