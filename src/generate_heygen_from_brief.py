#!/usr/bin/env python3
"""
Generate HeyGen avatar video from campaign brief.
Uses campaign_video_message from brief.json with audience and region context.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Optional

# Add src directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

# Unified logging
try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level
except ImportError:
    # Fallback for when run as module
    from .utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level

try:
    from heygen_integration import HeyGenIntegration
    from localization import Localization
    HEYGEN_AVAILABLE = True
except ImportError as e:
    log_warning(f"HeyGen integration not available: {e}")
    HEYGEN_AVAILABLE = False

def load_brief(brief_path: str) -> Dict:
    """Load and validate brief.json file."""
    if not os.path.exists(brief_path):
        raise FileNotFoundError(f"Brief file not found: {brief_path}")
    
    with open(brief_path, 'r', encoding='utf-8') as f:
        brief = json.load(f)
    
    # Validate required fields
    required_fields = ["products", "target_region", "audience"]
    for field in required_fields:
        if field not in brief:
            raise ValueError(f"Missing required field in brief: {field}")
    
    return brief

def generate_heygen_video_from_brief(
    brief_path: str,
    api_key: str,
    output_path: str,
    use_mock_translation: bool = True,
    local_model: str = "mistral-nemo"
) -> Dict:
    """
    Generate HeyGen avatar video from campaign brief.
    
    Args:
        brief_path: Path to brief.json file
        api_key: HeyGen API key
        output_path: Path to save video
        use_mock_translation: Use mock translation (offline)
        local_model: Local model for script planning
        
    Returns:
        Dictionary with generation results
    """
    if not HEYGEN_AVAILABLE:
        return {"success": False, "error": "HeyGen integration not available"}
    
    try:
        # Load brief
        brief = load_brief(brief_path)
        log_success(f"Loaded brief: {brief_path}")
        log_info(f"   Products: {', '.join(brief['products'])}")
        log_info(f"   Region: {brief['target_region']}")
        log_info(f"   Audience: {brief['audience']}")
        
        # Initialize localization
        loc = Localization(use_mock=use_mock_translation, translation_api="libre")
        
        # Localize campaign (generates campaign_video_message if not present)
        localized = loc.localize_campaign(brief, use_translation=not use_mock_translation)
        
        # Get script for HeyGen
        script = localized.get("campaign_video_message") or localized.get("campaign_message_localized")
        if not script:
            script = brief.get("campaign_message", "")
        
        log_info(f"   Script length: {len(script)} characters")
        log_info(f"   Language: {localized.get('language_code', 'en')}")
        
        # Initialize HeyGen integration
        heygen = HeyGenIntegration(api_key=api_key)
        
        # Generate video
        result = heygen.generate_with_local_models(
            prompt=script,
            local_model_type=local_model,
            output_path=output_path,
            language=localized.get("language_code", "en")
        )
        
        # Add brief metadata to result
        if result["success"]:
            result["brief"] = {
                "path": brief_path,
                "products": brief["products"],
                "target_region": brief["target_region"],
                "audience": brief["audience"],
                "language": localized.get("language_code", "en")
            }
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """Main function."""
    import logging
    
    parser = argparse.ArgumentParser(
        description="Generate HeyGen avatar video from campaign brief"
    )
    parser.add_argument("--brief", required=True, help="Path to brief.json file")
    parser.add_argument("--api-key", required=True, help="HeyGen API key")
    parser.add_argument("--output", default="output/heygen_from_brief.mp4", 
                       help="Output video path")
    parser.add_argument("--use-real-translation", action="store_true",
                       help="Use real translation API instead of mock")
    parser.add_argument("--local-model", default="mistral-nemo",
                       choices=["mistral-nemo", "qwen3-vl", "qwen3.5"],
                       help="Local model for script planning")
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
    
    if not HEYGEN_AVAILABLE:
        log_error("HeyGen integration not available.")
        log_info("Make sure heygen_integration.py is in the src directory.")
        sys.exit(1)
    
    log_info("=== HeyGen Avatar Generation from Brief ===")
    log_info(f"Brief: {args.brief}")
    log_info(f"Output: {args.output}")
    log_info(f"Translation: {'Real API' if args.use_real_translation else 'Mock (offline)'}")
    log_info("")
    
    # Generate video
    result = generate_heygen_video_from_brief(
        brief_path=args.brief,
        api_key=args.api_key,
        output_path=args.output,
        use_mock_translation=not args.use_real_translation,
        local_model=args.local_model
    )
    
    # Print results
    if result["success"]:
        log_success(f"\nHeyGen video generation successful!")
        log_info(f"   Video saved to: {result['video_path']}")
        log_info(f"   Task ID: {result.get('task_id', 'N/A')}")
        log_info(f"   File size: {result.get('file_size_bytes', 0) / 1024 / 1024:.1f} MB")
        
        if "brief" in result:
            brief_info = result["brief"]
            log_info(f"\n   Brief info:")
            log_info(f"     Products: {', '.join(brief_info['products'])}")
            log_info(f"     Region: {brief_info['target_region']}")
            log_info(f"     Audience: {brief_info['audience']}")
            log_info(f"     Language: {brief_info['language']}")
    else:
        log_error(f"\nHeyGen video generation failed:")
        log_error(f"   Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()