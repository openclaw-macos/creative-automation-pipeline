#!/bin/bash
# Template for testing campaigns with proper timestamp format
# Uses standardized timestamp format: YYYYMMDD_HHMM (no seconds)

set -e
set -u  # Treat unset variables as errors

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source timestamp utilities
source "$SCRIPT_DIR/timestamp_utils.sh"

# Default values
CAMPAIGN_NAME=""
VERBOSE=true
SIMULATE=false
QUIET=false
UPLOAD_TO_DRIVE=false
HEYGEN_API_KEY=""
CLIENT_SECRETS=""

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --campaign)
                CAMPAIGN_NAME="$2"
                shift 2
                ;;
            --quiet)
                VERBOSE=false
                QUIET=true
                shift
                ;;
            --simulate)
                SIMULATE=true
                shift
                ;;
            --upload-to-drive)
                UPLOAD_TO_DRIVE=true
                shift
                ;;
            --heygen-api-key)
                HEYGEN_API_KEY="$2"
                shift 2
                ;;
            --client-secrets)
                CLIENT_SECRETS="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                # If first argument doesn't start with --, treat as campaign name
                if [[ "$1" != --* ]] && [ -z "$CAMPAIGN_NAME" ]; then
                    CAMPAIGN_NAME="$1"
                    shift
                else
                    echo "❌ Unknown option: $1"
                    show_usage
                    exit 1
                fi
                ;;
        esac
    done
}

show_usage() {
    echo "Usage: $0 <campaign_name> [OPTIONS]"
    echo "   or: $0 --campaign <campaign_name> [OPTIONS]"
    echo ""
    echo "Run a complete campaign test with timestamped outputs and reports"
    echo ""
    echo "Required:"
    echo "  <campaign_name>          Campaign name from configs/examples/"
    echo ""
    echo "Optional:"
    echo "  --quiet                  Quiet mode (minimal output, no --verbose)"
    echo "  --simulate               Simulation mode (no real API calls)"
    echo "  --upload-to-drive        Upload outputs to Google Drive"
    echo "  --heygen-api-key KEY     HeyGen API key for avatar generation"
    echo "  --client-secrets PATH    OAuth client_secrets.json for YouTube"
    echo "  --help                   Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 1_Smart_Kitchen_Essentials_North_America"
    echo "  $0 --campaign 1_Smart_Kitchen_Essentials_North_America --simulate --quiet"
    echo "  $0 3_Premium_Personal_Care_Japan --upload-to-drive"
    echo ""
}

# Main execution
main() {
    parse_args "$@"
    
    # Validate campaign name
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
    
    if [ "$QUIET" = false ]; then
        echo "=== Testing Campaign: $CAMPAIGN_NAME ==="
        echo "Timestamp: $TIMESTAMP"
        echo ""
    fi

    # Create test output filename with correct timestamp format
    TEST_OUTPUT_FILE="${PROJECT_ROOT}/test_outputs/campaign_test_${CAMPAIGN_NAME}_${TIMESTAMP}.txt"
    mkdir -p "$(dirname "$TEST_OUTPUT_FILE")"

    if [ "$QUIET" = false ]; then
        echo "📝 Test output: $TEST_OUTPUT_FILE"
        echo "📋 Campaign brief: $BRIEF_FILE"
        echo ""
        echo "🚀 Running campaign demo..."
    fi

    START_TIME=$(date +%s)

    # Build command for run_campaign_demo.sh
    CMD_ARGS=("./run_campaign_demo.sh" "--brief" "$BRIEF_FILE")
    
    if [ "$VERBOSE" = true ]; then
        CMD_ARGS+=("--verbose")
    fi
    
    if [ "$SIMULATE" = true ]; then
        CMD_ARGS+=("--simulate")
    fi
    
    if [ "$UPLOAD_TO_DRIVE" = true ]; then
        CMD_ARGS+=("--upload-to-drive")
    fi
    
    if [ -n "$HEYGEN_API_KEY" ]; then
        CMD_ARGS+=("--heygen-api-key" "$HEYGEN_API_KEY")
    fi
    
    if [ -n "$CLIENT_SECRETS" ]; then
        CMD_ARGS+=("--client-secrets" "$CLIENT_SECRETS")
    fi

    # Run the command
    if [ "$QUIET" = true ]; then
        "${CMD_ARGS[@]}" 2>&1 | tee "$TEST_OUTPUT_FILE" > /dev/null
    else
        "${CMD_ARGS[@]}" 2>&1 | tee "$TEST_OUTPUT_FILE"
    fi

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    if [ "$QUIET" = false ]; then
        echo ""
        echo "⏱️  Campaign completed in ${DURATION} seconds"
    fi

    # Rename campaign folder with correct timestamp format
    if [ -d "outputs/campaign" ]; then
        NEW_FOLDER_NAME="outputs/campaign_${CAMPAIGN_NAME}_${TIMESTAMP}"
        mv "outputs/campaign" "$NEW_FOLDER_NAME"
        if [ "$QUIET" = false ]; then
            echo "📁 Campaign output folder: $NEW_FOLDER_NAME"
        fi
    elif [ "$QUIET" = false ]; then
        echo "⚠️  No outputs/campaign folder found"
    fi

    # Generate test report
    REPORT_FILENAME=$(get_test_report_filename "test_report_${CAMPAIGN_NAME}")
    REPORT_FILE="${PROJECT_ROOT}/test_reports/${REPORT_FILENAME}"

    if [ "$QUIET" = false ]; then
        echo "📊 Generating test report: $REPORT_FILE"
    fi

    echo "# Test Report: $CAMPAIGN_NAME" > "$REPORT_FILE"
    echo "## Test Details" >> "$REPORT_FILE"
    echo "- **Date:** $(get_readable_date)" >> "$REPORT_FILE"
    echo "- **Campaign:** $CAMPAIGN_NAME" >> "$REPORT_FILE"
    echo "- **Duration:** ${DURATION} seconds" >> "$REPORT_FILE"
    echo "- **Mode:** $([ "$SIMULATE" = true ] && echo "Simulation" || echo "Production")" >> "$REPORT_FILE"
    echo "- **Output Folder:** campaign_${CAMPAIGN_NAME}_${TIMESTAMP}" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "## Commands Executed" >> "$REPORT_FILE"
    echo "1. \`${CMD_ARGS[*]}\`" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "## Test Output" >> "$REPORT_FILE"
    echo '```bash' >> "$REPORT_FILE"
    tail -20 "$TEST_OUTPUT_FILE" >> "$REPORT_FILE" 2>/dev/null || echo "No test output available" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"

    if [ "$QUIET" = false ]; then
        echo ""
        echo "✅ Test completed successfully!"
        echo "   Output folder: campaign_${CAMPAIGN_NAME}_${TIMESTAMP}"
        echo "   Test report: $REPORT_FILE"
        echo "   Raw output: $TEST_OUTPUT_FILE"
    fi
}

# Execute
main "$@"