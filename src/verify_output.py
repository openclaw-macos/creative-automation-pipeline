#!/usr/bin/env python3
"""
Print the absolute path where the generated image will be saved.
This helps verify the output location when using the ComfyUI skill.
"""
import os
import sys

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Unified logging
try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level
except ImportError:
    # Fallback for when run as module
    from .utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level

def main():
    import argparse
    import logging
    
    parser = argparse.ArgumentParser(description="Verify output path and provide absolute path for pipeline integration")
    parser.add_argument("output_path", help="Output file path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug output")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                       default="INFO", help="Set log level (default: INFO)")
    args = parser.parse_args()
    
    # Set log level based on verbose flag or log-level argument
    if args.verbose:
        set_log_level(logging.DEBUG)
        log_debug("Verbose debug output enabled")
    else:
        level = get_log_level(args.log_level)
        set_log_level(level)
        if level <= logging.DEBUG:
            log_debug(f"Log level set to {args.log_level}")
    
    abs_path = os.path.abspath(args.output_path)
    log_info(f"Output will be saved to:")
    log_info(f"  {abs_path}")
    log_info(f"Directory: {os.path.dirname(abs_path)}")
    
    # Check if directory exists
    dir_path = os.path.dirname(abs_path)
    if dir_path:
        if os.path.isdir(dir_path):
            log_success("Directory exists.")
        else:
            log_warning("Directory does not exist; it will be created by the script.")
    else:
        log_warning("Output is in current directory.")
    
    # Suggest absolute path for pipeline integration
    log_info("\nFor integration with the Creative Automation Pipeline, use an absolute path:")
    log_info(f'  --output "{abs_path}"')

if __name__ == "__main__":
    main()