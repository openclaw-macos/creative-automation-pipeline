#!/usr/bin/env python3
"""
Campaign Manager for Creative Automation Pipeline.
Handles folder structure, campaign organization, and brief processing.
Creates timestamped folders for campaigns (campaign_{number}_{product_type}_{region}_{timestamp}) as per new standard.
"""
import os
import sys
import json
import shutil
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Unified logging
try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level
except ImportError:
    # Fallback for when run as module
    from .utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level

# Import timestamp utilities
try:
    from timestamp_utils import generate_campaign_folder_name, get_timestamp
except ImportError:
    # Fallback for direct execution
    from .timestamp_utils import generate_campaign_folder_name, get_timestamp

class CampaignManager:
    """
    Manages campaign folders and brief processing.
    Creates numbered folders (1_, 2_, etc.) for organized campaign storage.
    """
    
    def __init__(self, campaigns_root: str = "../campaigns"):
        """
        Initialize campaign manager.
        
        Args:
            campaigns_root: Root directory for campaign folders
        """
        self.campaigns_root = os.path.abspath(campaigns_root)
        os.makedirs(self.campaigns_root, exist_ok=True)
        
        # Load or create campaign index
        self.index_file = os.path.join(self.campaigns_root, "campaign_index.json")
        self.campaigns = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load campaign index from file or create new."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_index(self):
        """Save campaign index to file."""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.campaigns, f, indent=2)
    
    def get_next_campaign_number(self) -> int:
        """Get next available campaign number."""
        if not self.campaigns:
            return 1
        
        # Find highest number
        numbers = []
        for campaign_id, info in self.campaigns.items():
            if campaign_id.startswith("campaign_"):
                try:
                    num = int(campaign_id.replace("campaign_", ""))
                    numbers.append(num)
                except:
                    pass
        
        return max(numbers) + 1 if numbers else 1
    
    def generate_campaign_name(self, brief: Dict, campaign_number: int = None) -> str:
        """
        Generate campaign folder name from brief with timestamp.
        Format: campaign_{number}_{product_type}_{region}_{timestamp}
        
        Args:
            brief: Campaign brief dictionary
            campaign_number: Campaign number (if None, uses next available)
            
        Returns:
            Campaign folder name with timestamp
        """
        # Get campaign number
        if campaign_number is None:
            campaign_number = self.get_next_campaign_number()
        
        # Extract product type (first product)
        products = brief.get("products", ["Unknown"])
        product_type = products[0].replace(" ", "_")
        
        # Extract region
        target_region = brief.get("target_region", "Unknown")
        
        # Generate folder name with timestamp
        folder_name = generate_campaign_folder_name(
            campaign_number=campaign_number,
            product_type=product_type,
            target_region=target_region,
            include_timestamp=True,
            timestamp_with_seconds=True  # Use seconds as per requirements
        )
        
        return folder_name
    
    def create_campaign_folder(self, brief: Dict, brief_path: str) -> Tuple[str, str]:
        """
        Create timestamped campaign folder and copy brief.json.
        
        Args:
            brief: Campaign brief dictionary
            brief_path: Path to source brief.json file
            
        Returns:
            Tuple of (campaign_id, folder_path)
        """
        # Get next campaign number
        campaign_number = self.get_next_campaign_number()
        
        # Generate campaign folder name with timestamp
        folder_name = self.generate_campaign_name(brief, campaign_number)
        folder_path = os.path.join(self.campaigns_root, folder_name)
        
        # Create folder
        os.makedirs(folder_path, exist_ok=True)
        
        # Copy brief.json
        dest_brief_path = os.path.join(folder_path, "brief.json")
        shutil.copy2(brief_path, dest_brief_path)
        
        # Create outputs subdirectories
        outputs_dir = os.path.join(folder_path, "outputs")
        os.makedirs(os.path.join(outputs_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(outputs_dir, "video"), exist_ok=True)
        os.makedirs(os.path.join(outputs_dir, "audio"), exist_ok=True)
        os.makedirs(os.path.join(outputs_dir, "final"), exist_ok=True)
        
        # Update index
        campaign_id = f"campaign_{campaign_number}"
        self.campaigns[campaign_id] = {
            "folder_name": folder_name,
            "folder_path": folder_path,
            "brief_path": dest_brief_path,
            "products": brief.get("products", []),
            "target_region": brief.get("target_region", "Unknown"),
            "created": datetime.now().isoformat(),
            "campaign_number": campaign_number
        }
        
        self._save_index()
        
        return campaign_id, folder_path
    
    def process_brief_file(self, brief_path: str) -> Tuple[str, str]:
        """
        Process a brief.json file: create campaign folder and return paths.
        
        Args:
            brief_path: Path to brief.json file
            
        Returns:
            Tuple of (campaign_id, folder_path)
        """
        # Load brief
        with open(brief_path, 'r', encoding='utf-8') as f:
            brief = json.load(f)
        
        # Create campaign folder
        return self.create_campaign_folder(brief, brief_path)
    
    def list_campaigns(self) -> List[Dict]:
        """List all campaigns in index."""
        return [
            {
                "id": campaign_id,
                **info
            }
            for campaign_id, info in self.campaigns.items()
        ]
    
    def get_campaign_by_number(self, number: int) -> Optional[Dict]:
        """Get campaign by number."""
        campaign_id = f"campaign_{number}"
        return self.campaigns.get(campaign_id)
    
    def rename_campaign_folders(self):
        """
        Rename campaign folders to maintain sequential numbering.
        Useful when campaigns are deleted and numbering needs to be compacted.
        """
        # Get all campaigns sorted by number
        campaigns_by_number = []
        for campaign_id, info in self.campaigns.items():
            if campaign_id.startswith("campaign_"):
                try:
                    num = int(campaign_id.replace("campaign_", ""))
                    campaigns_by_number.append((num, campaign_id, info))
                except:
                    pass
        
        campaigns_by_number.sort(key=lambda x: x[0])
        
        # Rename folders with sequential numbers
        new_campaigns = {}
        for new_number, (old_number, campaign_id, info) in enumerate(campaigns_by_number, 1):
            if new_number != old_number:
                # Generate new folder name
                old_folder_path = info["folder_path"]
                old_folder_name = info["folder_name"]
                
                # Extract base name (without number prefix)
                # Handle both old format (number_...) and new format (campaign_number_...)
                parts = old_folder_name.split("_")
                if old_folder_name.startswith("campaign_"):
                    # New format: campaign_{number}_{product}_{region}_{timestamp}
                    # Keep everything after campaign_{number}
                    base_name = "_".join(parts[2:]) if len(parts) > 2 else ""
                else:
                    # Old format: {number}_{product}_{region}
                    base_name = "_".join(parts[1:]) if len(parts) > 1 else ""
                
                # Create new folder name with appropriate prefix
                if old_folder_name.startswith("campaign_"):
                    new_folder_name = f"campaign_{new_number}_{base_name}"
                else:
                    new_folder_name = f"{new_number}_{base_name}"
                new_folder_path = os.path.join(self.campaigns_root, new_folder_name)
                
                # Rename folder
                if os.path.exists(old_folder_path):
                    shutil.move(old_folder_path, new_folder_path)
                
                # Update info
                info["folder_name"] = new_folder_name
                info["folder_path"] = new_folder_path
                info["campaign_number"] = new_number
            
            # Update campaign ID
            new_campaign_id = f"campaign_{new_number}"
            new_campaigns[new_campaign_id] = info
        
        # Update index
        self.campaigns = new_campaigns
        self._save_index()


def main():
    """Test campaign manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Campaign Manager")
    parser.add_argument("--brief", default="../configs/brief.json", help="Path to brief.json file")
    parser.add_argument("--list", action="store_true", help="List existing campaigns")
    parser.add_argument("--rename", action="store_true", help="Rename campaign folders to maintain sequential numbering")
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
    
    # Initialize campaign manager
    manager = CampaignManager()
    
    if args.list:
        log_info("Existing campaigns:")
        campaigns = manager.list_campaigns()
        for campaign in campaigns:
            log_info(f"  {campaign['campaign_number']}: {campaign['folder_name']}")
            log_info(f"     Region: {campaign['target_region']}")
            log_info(f"     Products: {', '.join(campaign['products'][:3])}")
            log_info(f"     Path: {campaign['folder_path']}")
            log_info("")
    
    elif args.rename:
        log_info("Renaming campaign folders to maintain sequential numbering...")
        manager.rename_campaign_folders()
        log_success("Done!")
    
    else:
        # Process brief file
        log_info(f"Processing brief file: {args.brief}")
        if os.path.exists(args.brief):
            campaign_id, folder_path = manager.process_brief_file(args.brief)
            log_success(f"Created campaign folder: {folder_path}")
            log_info(f"   Campaign ID: {campaign_id}")
            
            # List all campaigns
            log_info("\nAll campaigns:")
            for campaign in manager.list_campaigns():
                log_info(f"  {campaign['campaign_number']}: {campaign['folder_name']}")
        else:
            log_warning(f"Brief file not found: {args.brief}")
            log_info("Creating sample brief...")
            
            # Create sample brief
            sample_brief = {
                "products": ["Coffee Maker", "Blender"],
                "target_region": "USA",
                "audience": "Young professionals 25-35",
                "campaign_message": "Start your day smarter with our kitchen essentials"
            }
            
            sample_brief_path = "sample_brief.json"
            with open(sample_brief_path, 'w', encoding='utf-8') as f:
                json.dump(sample_brief, f, indent=2)
            
            campaign_id, folder_path = manager.process_brief_file(sample_brief_path)
            log_success(f"Created campaign folder from sample: {folder_path}")
            os.remove(sample_brief_path)


if __name__ == "__main__":
    main()