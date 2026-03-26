#!/usr/bin/env python3
"""
Timestamp Utilities for Creative Automation Pipeline.
Provides standardized timestamp formats for campaign folders, test reports, and outputs.
"""

import os
import sys
import time
from datetime import datetime
from typing import Optional, Union


def get_timestamp(
    format_type: str = "folder", 
    include_seconds: bool = True
) -> str:
    """
    Get standardized timestamp string.
    
    Args:
        format_type: Type of timestamp format ("folder", "file", "human")
        include_seconds: Whether to include seconds in timestamp
        
    Returns:
        Formatted timestamp string
    
    Examples:
        get_timestamp("folder") → "20260325_141530" (YYYYMMDD_HHMMSS)
        get_timestamp("folder", False) → "20260325_1415" (YYYYMMDD_HHMM)
        get_timestamp("file") → "2026-03-25_14-15-30"
        get_timestamp("human") → "2026-03-25 14:15:30"
    """
    now = datetime.now()
    
    if format_type == "folder":
        # Format: YYYYMMDD_HHMMSS (compatible with folder naming)
        if include_seconds:
            return now.strftime("%Y%m%d_%H%M%S")
        else:
            return now.strftime("%Y%m%d_%H%M")
    
    elif format_type == "file":
        # Format: YYYY-MM-DD_HH-MM-SS (safe for filenames)
        if include_seconds:
            return now.strftime("%Y-%m-%d_%H-%M-%S")
        else:
            return now.strftime("%Y-%m-%d_%H-%M")
    
    elif format_type == "human":
        # Format: YYYY-MM-DD HH:MM:SS (human readable)
        if include_seconds:
            return now.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return now.strftime("%Y-%m-%d %H:%M")
    
    else:
        # Default to folder format
        if include_seconds:
            return now.strftime("%Y%m%d_%H%M%S")
        else:
            return now.strftime("%Y%m%d_%H%M")


def generate_campaign_folder_name(
    campaign_number: int,
    product_type: str,
    target_region: str,
    include_timestamp: bool = True,
    timestamp_with_seconds: bool = True
) -> str:
    """
    Generate campaign folder name with standardized timestamp.
    
    Format: campaign_{number}_{product_type}_{region}_{timestamp}
    
    Args:
        campaign_number: Campaign number (1, 2, 3...)
        product_type: Clean product type string (spaces replaced with underscores)
        target_region: Clean region string (spaces replaced with underscores)
        include_timestamp: Whether to include timestamp in folder name
        timestamp_with_seconds: Whether to include seconds in timestamp
        
    Returns:
        Campaign folder name
    
    Example:
        generate_campaign_folder_name(2, "Sustainable_Home_Care", "Europe", True, True)
        → "campaign_2_Sustainable_Home_Care_Europe_20260324_143914"
    """
    # Clean inputs (ensure no special characters)
    import re
    
    clean_product = re.sub(r'[^\w\s-]', '', product_type)
    clean_product = clean_product.replace(" ", "_").replace("/", "_")
    
    clean_region = re.sub(r'[^\w\s-]', '', target_region)
    clean_region = clean_region.replace(" ", "_").replace("/", "_")
    
    # Build folder name
    folder_name = f"campaign_{campaign_number}_{clean_product}_{clean_region}"
    
    if include_timestamp:
        timestamp = get_timestamp("folder", timestamp_with_seconds)
        folder_name = f"{folder_name}_{timestamp}"
    
    return folder_name


def parse_timestamp_from_folder(folder_name: str) -> Optional[datetime]:
    """
    Parse timestamp from folder name.
    
    Args:
        folder_name: Folder name containing timestamp (YYYYMMDD_HHMMSS or YYYYMMDD_HHMM)
        
    Returns:
        datetime object if timestamp found, None otherwise
    """
    import re
    
    # Try to find timestamp patterns
    patterns = [
        r'(\d{8}_\d{6})',  # YYYYMMDD_HHMMSS
        r'(\d{8}_\d{4})',  # YYYYMMDD_HHMM
        r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})',  # YYYY-MM-DD_HH-MM-SS
        r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2})',  # YYYY-MM-DD_HH-MM
    ]
    
    for pattern in patterns:
        match = re.search(pattern, folder_name)
        if match:
            timestamp_str = match.group(1)
            try:
                # Try different formats
                if "_" in timestamp_str and len(timestamp_str) == 15:  # YYYYMMDD_HHMMSS
                    return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                elif "_" in timestamp_str and len(timestamp_str) == 13:  # YYYYMMDD_HHMM
                    return datetime.strptime(timestamp_str, "%Y%m%d_%H%M")
                elif "-" in timestamp_str and len(timestamp_str) == 19:  # YYYY-MM-DD_HH-MM-SS
                    return datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                elif "-" in timestamp_str and len(timestamp_str) == 16:  # YYYY-MM-DD_HH-MM
                    return datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M")
            except ValueError:
                continue
    
    return None


def is_valid_timestamp_format(timestamp_str: str) -> bool:
    """
    Check if string matches valid timestamp format.
    
    Valid formats:
    - YYYYMMDD_HHMMSS
    - YYYYMMDD_HHMM
    - YYYY-MM-DD_HH-MM-SS
    - YYYY-MM-DD_HH-MM
    
    Args:
        timestamp_str: Timestamp string to validate
        
    Returns:
        True if valid format, False otherwise
    """
    import re
    
    patterns = [
        r'^\d{8}_\d{6}$',  # YYYYMMDD_HHMMSS
        r'^\d{8}_\d{4}$',  # YYYYMMDD_HHMM
        r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$',  # YYYY-MM-DD_HH-MM-SS
        r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$',  # YYYY-MM-DD_HH-MM
    ]
    
    return any(re.match(pattern, timestamp_str) for pattern in patterns)


def convert_timestamp_format(
    timestamp_str: str,
    target_format: str = "folder",
    include_seconds: bool = True
) -> Optional[str]:
    """
    Convert timestamp between different formats.
    
    Args:
        timestamp_str: Source timestamp string
        target_format: Target format ("folder", "file", "human")
        include_seconds: Whether to include seconds in output
        
    Returns:
        Converted timestamp string, or None if conversion failed
    """
    # Parse input timestamp
    dt = parse_timestamp_from_folder(timestamp_str)
    if not dt:
        return None
    
    # Convert to target format
    if target_format == "folder":
        if include_seconds:
            return dt.strftime("%Y%m%d_%H%M%S")
        else:
            return dt.strftime("%Y%m%d_%H%M")
    
    elif target_format == "file":
        if include_seconds:
            return dt.strftime("%Y-%m-%d_%H-%M-%S")
        else:
            return dt.strftime("%Y-%m-%d_%H-%M")
    
    elif target_format == "human":
        if include_seconds:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return dt.strftime("%Y-%m-%d %H:%M")
    
    return None


def get_timestamped_filename(
    base_name: str,
    extension: str = "",
    include_timestamp: bool = True,
    timestamp_format: str = "file"
) -> str:
    """
    Generate timestamped filename for test reports and outputs.
    
    Args:
        base_name: Base filename (without extension)
        extension: File extension (with or without dot)
        include_timestamp: Whether to add timestamp
        timestamp_format: Timestamp format ("folder", "file", "human")
        
    Returns:
        Timestamped filename
    
    Example:
        get_timestamped_filename("test_report", "md", True, "file")
        → "test_report_2026-03-25_14-15-30.md"
    """
    # Clean extension
    if extension and not extension.startswith("."):
        extension = f".{extension}"
    
    # Add timestamp if requested
    if include_timestamp:
        timestamp = get_timestamp(timestamp_format, True)
        return f"{base_name}_{timestamp}{extension}"
    else:
        return f"{base_name}{extension}"


def get_campaign_timestamp_from_brief(brief_path: str) -> Optional[str]:
    """
    Extract timestamp from campaign folder name based on brief.
    Used for maintaining consistent timestamps across campaign assets.
    
    Args:
        brief_path: Path to campaign brief.json
        
    Returns:
        Timestamp string (YYYYMMDD_HHMMSS) if found, None otherwise
    """
    import os
    import re
    
    # Get campaign folder name from brief path
    campaign_folder = os.path.basename(os.path.dirname(brief_path))
    
    # Try to extract timestamp
    dt = parse_timestamp_from_folder(campaign_folder)
    if dt:
        return dt.strftime("%Y%m%d_%H%M%S")
    
    return None


def main():
    """Test timestamp utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test timestamp utilities")
    parser.add_argument("--format", choices=["folder", "file", "human"], default="folder", help="Timestamp format")
    parser.add_argument("--no-seconds", action="store_true", help="Exclude seconds from timestamp")
    parser.add_argument("--generate-folder", action="store_true", help="Generate campaign folder name")
    parser.add_argument("--campaign-number", type=int, default=2, help="Campaign number for folder generation")
    parser.add_argument("--product-type", default="Sustainable_Home_Care", help="Product type for folder generation")
    parser.add_argument("--region", default="Europe", help="Target region for folder generation")
    parser.add_argument("--parse", help="Parse timestamp from folder name")
    parser.add_argument("--convert", help="Convert timestamp format")
    parser.add_argument("--convert-to", choices=["folder", "file", "human"], default="folder", help="Target format for conversion")
    parser.add_argument("--filename", action="store_true", help="Generate timestamped filename")
    parser.add_argument("--base-name", default="test_report", help="Base filename for timestamped file")
    parser.add_argument("--extension", default="md", help="File extension")
    
    args = parser.parse_args()
    
    print("=== Timestamp Utilities Test ===\n")
    
    # Test basic timestamp
    timestamp = get_timestamp(args.format, not args.no_seconds)
    print(f"Current timestamp ({args.format} format): {timestamp}")
    
    # Test campaign folder name generation
    if args.generate_folder:
        folder_name = generate_campaign_folder_name(
            args.campaign_number,
            args.product_type,
            args.region,
            True,
            not args.no_seconds
        )
        print(f"\nGenerated campaign folder name: {folder_name}")
    
    # Test timestamp parsing
    if args.parse:
        dt = parse_timestamp_from_folder(args.parse)
        if dt:
            print(f"\nParsed timestamp from '{args.parse}': {dt}")
            print(f"  ISO format: {dt.isoformat()}")
            print(f"  Human readable: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"\nNo valid timestamp found in: {args.parse}")
    
    # Test timestamp conversion
    if args.convert:
        converted = convert_timestamp_format(args.convert, args.convert_to, not args.no_seconds)
        if converted:
            print(f"\nConverted '{args.convert}' to {args.convert_to} format: {converted}")
        else:
            print(f"\nFailed to convert timestamp: {args.convert}")
    
    # Test timestamped filename generation
    if args.filename:
        filename = get_timestamped_filename(
            args.base_name,
            args.extension,
            True,
            args.format
        )
        print(f"\nTimestamped filename: {filename}")
    
    # Test format validation
    test_timestamps = [
        "20260324_143914",
        "20260324_1439",
        "2026-03-24_14-39-14",
        "2026-03-24_14-39",
        "invalid_timestamp"
    ]
    
    print("\nTimestamp format validation:")
    for ts in test_timestamps:
        valid = is_valid_timestamp_format(ts)
        print(f"  {ts}: {'✓ VALID' if valid else '✗ INVALID'}")


if __name__ == "__main__":
    main()