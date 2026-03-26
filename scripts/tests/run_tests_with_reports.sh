#!/bin/bash
# Run tests with report generation for Creative Automation Pipeline
# Generates timestamped .md reports in test_reports/ folder

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
TEST_SCRIPTS_DIR="$SCRIPT_DIR"
TEST_REPORTS_DIR="$PROJECT_ROOT/test_reports"
PYTHON_EXEC="python3"

# Ensure test reports directory exists
mkdir -p "$TEST_REPORTS_DIR"

echo "=== Creative Automation Pipeline - Test Suite with Reports ==="
echo "Test Scripts: $TEST_SCRIPTS_DIR"
echo "Test Reports: $TEST_REPORTS_DIR"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# List available test scripts
AVAILABLE_TESTS=()
for test_script in "$TEST_SCRIPTS_DIR"/test_*.sh; do
    if [ -f "$test_script" ]; then
        test_name=$(basename "$test_script" .sh)
        AVAILABLE_TESTS+=("$test_name")
    fi
done

echo "Available tests:"
for test in "${AVAILABLE_TESTS[@]}"; do
    echo "  - $test"
done
echo ""

# Parse command line arguments
RUN_ALL=false
RUN_TESTS=()
GENERATE_REPORT=true
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_ALL=true
            shift
            ;;
        --test)
            RUN_TESTS+=("$2")
            shift 2
            ;;
        --no-report)
            GENERATE_REPORT=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --list)
            echo "Available test scripts:"
            for test_script in "$TEST_SCRIPTS_DIR"/test_*.sh; do
                if [ -f "$test_script" ]; then
                    echo "  $(basename "$test_script")"
                    # Show first few lines as description
                    head -5 "$test_script" | grep -E "^# " | sed 's/^# /    /'
                fi
            done
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--all] [--test TEST_NAME] [--no-report] [--verbose] [--list]"
            exit 1
            ;;
    esac
done

# Determine which tests to run
TESTS_TO_RUN=()
if [ "$RUN_ALL" = true ]; then
    TESTS_TO_RUN=("${AVAILABLE_TESTS[@]}")
elif [ ${#RUN_TESTS[@]} -gt 0 ]; then
    TESTS_TO_RUN=("${RUN_TESTS[@]}")
else
    # Default: run all tests
    TESTS_TO_RUN=("${AVAILABLE_TESTS[@]}")
fi

echo "Tests to run: ${TESTS_TO_RUN[*]}"
echo ""

# Function to run a test and generate report
run_test_with_report() {
    local test_name="$1"
    local test_script="$TEST_SCRIPTS_DIR/$test_name.sh"
    
    if [ ! -f "$test_script" ]; then
        echo "❌ Test script not found: $test_script"
        return 1
    fi
    
    echo "=== Running: $test_name ==="
    
    if [ "$GENERATE_REPORT" = true ]; then
        # Generate timestamp for this run
        TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
        LOG_FILE="$TEST_REPORTS_DIR/${test_name}_${TIMESTAMP}.log"
        REPORT_FILE="$TEST_REPORTS_DIR/${test_name}_${TIMESTAMP}.md"
        
        # Make script executable
        chmod +x "$test_script" 2>/dev/null || true
        
        # Run test and capture output
        echo "Log file: $LOG_FILE"
        echo "Report file: $REPORT_FILE"
        
        # Capture start time
        START_TIME=$(date +%s)
        
        # Run the test script
        if [ "$VERBOSE" = true ]; then
            # Show output in real-time and capture it
            echo "--- Test Output ---"
            "$test_script" 2>&1 | tee "$LOG_FILE"
            EXIT_CODE=${PIPESTATUS[0]}
        else
            # Run quietly, capture output
            "$test_script" > "$LOG_FILE" 2>&1
            EXIT_CODE=$?
        fi
        
        # Capture end time
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        # Generate report using Python generator
        echo "Generating test report..."
        "$PYTHON_EXEC" -c "
import sys
sys.path.append('$PROJECT_ROOT/src')
from test_report_generator import TestReportGenerator
import os

generator = TestReportGenerator('$TEST_REPORTS_DIR')
generator.start_test('$test_name', 'automated_test')

# Read log file
log_content = ''
if os.path.exists('$LOG_FILE'):
    with open('$LOG_FILE', 'r', encoding='utf-8') as f:
        log_content = f.read()

generator.capture_output(log_content)

# Parse log for check results
lines = log_content.split('\\n')
for line in lines:
    line_lower = line.lower()
    if '✅' in line or '✓' in line or 'pass' in line_lower:
        if 'test' in line_lower or 'check' in line_lower:
            generator.add_check(f'Check: {line.strip()[:50]}', True)
    elif '❌' in line or '✗' in line or 'fail' in line_lower:
        if 'test' in line_lower or 'check' in line_lower:
            generator.add_check(f'Check: {line.strip()[:50]}', False)

# Add overall test result
if $EXIT_CODE == 0:
    generator.add_check('Test execution completed successfully', True, f'Exit code: $EXIT_CODE')
else:
    generator.add_check('Test execution failed', False, f'Exit code: $EXIT_CODE')

generator.add_check('Test duration', True, f'{DURATION} seconds')
generator.end_test()

report_path = generator.generate_report()
print(f'Report generated: {report_path}')
"
        
        # Check test result
        if [ $EXIT_CODE -eq 0 ]; then
            echo "✅ $test_name: PASSED (${DURATION}s)"
        else
            echo "❌ $test_name: FAILED (${DURATION}s)"
        fi
        
    else
        # Run without report generation
        echo "--- Test Output (no report) ---"
        "$test_script"
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 0 ]; then
            echo "✅ $test_name: PASSED"
        else
            echo "❌ $test_name: FAILED"
        fi
    fi
    
    echo ""
    return $EXIT_CODE
}

# Run selected tests
FAILED_TESTS=()
PASSED_TESTS=()

for test_name in "${TESTS_TO_RUN[@]}"; do
    if run_test_with_report "$test_name"; then
        PASSED_TESTS+=("$test_name")
    else
        FAILED_TESTS+=("$test_name")
    fi
done

# Summary
echo "=== Test Suite Summary ==="
echo ""

if [ ${#PASSED_TESTS[@]} -gt 0 ]; then
    echo "✅ PASSED (${#PASSED_TESTS[@]}):"
    for test in "${PASSED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
fi

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo "❌ FAILED (${#FAILED_TESTS[@]}):"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
fi

# Show generated reports
if [ "$GENERATE_REPORT" = true ] && [ -d "$TEST_REPORTS_DIR" ]; then
    REPORT_FILES=()
    for report in "$TEST_REPORTS_DIR"/*.md; do
        if [ -f "$report" ]; then
            REPORT_FILES+=("$report")
        fi
    done
    
    if [ ${#REPORT_FILES[@]} -gt 0 ]; then
        echo "📋 Generated Reports:"
        for report in "${REPORT_FILES[@]}"; do
            report_name=$(basename "$report")
            echo "  - $report_name"
        done
        echo ""
        
        # Show latest report summary
        LATEST_REPORT=$(ls -t "$TEST_REPORTS_DIR"/*.md 2>/dev/null | head -1)
        if [ -n "$LATEST_REPORT" ]; then
            echo "Latest report: $(basename "$LATEST_REPORT")"
            echo "To view: open '$LATEST_REPORT' or 'cat $LATEST_REPORT'"
        fi
    fi
fi

# Exit with appropriate code
if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "⚠️  ${#FAILED_TESTS[@]} test(s) failed"
    exit 1
fi