#!/bin/bash
# Timestamp utilities for Creative Automation Pipeline
# Standardized timestamp formats across the project
#
# Usage in scripts:
#   source scripts/timestamp_utils.sh
#   TIMESTAMP=$(get_timestamp_no_seconds)
#
# Usage in interactive shell:
#   . scripts/timestamp_utils.sh
#   get_timestamp_no_seconds
#
# All timestamps use format: YYYYMMDD_HHMM (no seconds)

# Get timestamp without seconds: YYYYMMDD_HHMM
# Example: 20260324_1437
get_timestamp_no_seconds() {
    date +"%Y%m%d_%H%M"
}

# Get timestamp with seconds: YYYYMMDD_HHMMSS  
# Example: 20260324_143717 (legacy, not recommended)
get_timestamp_with_seconds() {
    date +"%Y%m%d_%H%M%S"
}

# Get readable date for reports: YYYY-MM-DD HH:MM
# Example: 2026-03-24 14:37
get_readable_date() {
    date +"%Y-%m-%d %H:%M"
}

# Get filename-safe timestamp for reports: YYYYMMDD_HHMM
# Example: 20260324_1437
get_filename_timestamp() {
    get_timestamp_no_seconds
}

# Get campaign folder name with timestamp
# Example: campaign_1_Smart_Kitchen_Essentials_North_America_20260324_1437
get_campaign_folder_name() {
    local campaign_name="$1"
    local timestamp=$(get_timestamp_no_seconds)
    echo "campaign_${campaign_name}_${timestamp}"
}

# Get test report filename with timestamp
# Example: comprehensive_test_report_20260324_1400.md
get_test_report_filename() {
    local report_prefix="$1"
    local timestamp=$(get_timestamp_no_seconds)
    echo "${report_prefix}_${timestamp}.md"
}

# Example usage:
# TIMESTAMP=$(get_timestamp_no_seconds)
# CAMPAIGN_FOLDER=$(get_campaign_folder_name "1_Smart_Kitchen_Essentials_North_America")
# REPORT_FILE=$(get_test_report_filename "comprehensive_test_report")