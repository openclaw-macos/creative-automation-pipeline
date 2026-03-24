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

try:
    from heygen_integration import HeyGenIntegration
    from localization import Localization
    HEYGEN_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: HeyGen integration not available: {e}")
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
        print(f"✅ Loaded brief: {brief_path}")
        print(f"   Products: {', '.join(brief['products'])}")
        print(f"   Region: {brief['target_region']}")
        print(f"   Audience: {brief['audience']}")
        
        # Initialize localization
        loc = Localization(use_mock=use_mock_translation, translation_api="libre")
        
        # Localize campaign (generates campaign_video_message if not present)
        localized = loc.localize_campaign(brief, use_translation=not use_mock_translation)
        
        # Get script for HeyGen
        script = localized.get("campaign_video_message") or localized.get("campaign_message_localized")
        if not script:
            script = brief.get("campaign_message", "")
        
        print(f"   Script length: {len(script)} characters")
        print(f"   Language: {localized.get('language_code', 'en')}")
        
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
    
    args = parser.parse_args()
    
    if not HEYGEN_AVAILABLE:
        print("ERROR: HeyGen integration not available.")
        print("Make sure heygen_integration.py is in the src directory.")
        sys.exit(1)
    
    print("=== HeyGen Avatar Generation from Brief ===")
    print(f"Brief: {args.brief}")
    print(f"Output: {args.output}")
    print(f"Translation: {'Real API' if args.use_real_translation else 'Mock (offline)'}")
    print()
    
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
        print(f"\n✅ HeyGen video generation successful!")
        print(f"   Video saved to: {result['video_path']}")
        print(f"   Task ID: {result.get('task_id', 'N/A')}")
        print(f"   File size: {result.get('file_size_bytes', 0) / 1024 / 1024:.1f} MB")
        
        if "brief" in result:
            brief_info = result["brief"]
            print(f"\n   Brief info:")
            print(f"     Products: {', '.join(brief_info['products'])}")
            print(f"     Region: {brief_info['target_region']}")
            print(f"     Audience: {brief_info['audience']}")
            print(f"     Language: {brief_info['language']}")
    else:
        print(f"\n❌ HeyGen video generation failed:")
        print(f"   Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()