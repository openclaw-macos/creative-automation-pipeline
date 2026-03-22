#!/usr/bin/env python3
"""
Brand Compliance Module for Creative Automation Pipeline.
Uses OpenCV (or fallback) to verify logo presence and brand colors.
"""
import json
import os
import sys
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("WARNING: OpenCV not installed. Brand compliance checks will be limited.")
    # Provide dummy functions for type hints
    cv2 = None

class BrandComplianceChecker:
    def __init__(self, config_path: str = "../configs/brand_config.json"):
        """
        Load brand configuration from JSON.
        """
        self.config_path = config_path
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.logo_path = self.config.get("logo_path", "")
        # Extract hex color strings from brand_colors dict
        brand_colors_raw = self.config.get("brand_colors", {})
        self.brand_colors = list(brand_colors_raw.values()) if isinstance(brand_colors_raw, dict) else brand_colors_raw
        
        # Update color_tolerance to use proper structure
        color_check_settings = self.config.get("color_check_settings", {})
        self.color_tolerance = color_check_settings.get("tolerance_percent", 20)
        self.color_min_coverage = color_check_settings.get("min_coverage_percent", 5.0)
        
        self.logo_min_match_threshold = 0.8
        if self.config.get("logo_check_settings"):
            self.logo_min_match_threshold = self.config["logo_check_settings"].get("match_threshold", 0.8)
        
        # Load logo image if available
        self.logo_img = None
        if OPENCV_AVAILABLE and self.logo_path and os.path.exists(self.logo_path):
            self.logo_img = cv2.imread(self.logo_path, cv2.IMREAD_COLOR)
            if self.logo_img is None:
                print(f"WARNING: Could not load logo image from {self.logo_path}")
        elif self.logo_path:
            print(f"WARNING: Logo image specified but OpenCV not available or file missing: {self.logo_path}")
    
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color (#RRGGBB) to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif len(hex_color) == 3:
            return tuple(int(hex_color[i]*2, 16) for i in (0, 1, 2))
        else:
            raise ValueError(f"Invalid hex color: {hex_color}")
    
    def color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Compute Euclidean distance between two RGB colors."""
        return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)))
    
    def check_brand_colors(self, image_path: str) -> Dict[str, Any]:
        """
        Check if brand colors are present in the image.
        Returns dict with pass/fail and details.
        """
        if not OPENCV_AVAILABLE:
            return {
                "passed": False,
                "reason": "OpenCV not installed",
                "details": {}
            }
        
        img = cv2.imread(image_path)
        if img is None:
            return {
                "passed": False,
                "reason": f"Could not read image {image_path}",
                "details": {}
            }
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Reshape to list of pixels
        pixels = img_rgb.reshape(-1, 3)
        
        # Count pixels close to each brand color
        brand_color_rgbs = [self.hex_to_rgb(hc) for hc in self.brand_colors]
        color_counts = {hc: 0 for hc in self.brand_colors}
        
        for pixel in pixels:
            for hex_color, rgb in zip(self.brand_colors, brand_color_rgbs):
                if self.color_distance(pixel, rgb) <= self.color_tolerance:
                    color_counts[hex_color] += 1
        
        total_pixels = pixels.shape[0]
        color_percentages = {hc: count / total_pixels * 100 for hc, count in color_counts.items()}
        
        # Determine pass/fail: at least one brand color present > min_coverage% of pixels
        passed = any(pct >= self.color_min_coverage for pct in color_percentages.values())
        
        return {
            "passed": bool(passed),
            "reason": "Brand colors detected" if passed else "Insufficient brand colors",
            "details": {
                "color_percentages": color_percentages,
                "threshold": self.color_min_coverage
            }
        }
    
    def check_logo_presence(self, image_path: str) -> Dict[str, Any]:
        """
        Check if brand logo is present in the image using template matching.
        Returns dict with pass/fail and match score.
        """
        if not OPENCV_AVAILABLE:
            return {
                "passed": False,
                "reason": "OpenCV not installed",
                "details": {}
            }
        
        if self.logo_img is None:
            return {
                "passed": False,
                "reason": "Logo image not loaded",
                "details": {}
            }
        
        img = cv2.imread(image_path)
        if img is None:
            return {
                "passed": False,
                "reason": f"Could not read image {image_path}",
                "details": {}
            }
        
        # Template matching
        result = cv2.matchTemplate(img, self.logo_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        passed = max_val >= self.logo_min_match_threshold
        
        return {
            "passed": bool(passed),
            "reason": f"Logo detected (score: {max_val:.3f})" if passed else f"Logo not detected (score: {max_val:.3f})",
            "details": {
                "match_score": float(max_val),
                "threshold": self.logo_min_match_threshold,
                "location": (int(max_loc[0]), int(max_loc[1])) if passed else None
            }
        }
    
    def run_compliance_checks(self, image_path: str, checks: List[str] = None) -> Dict[str, Any]:
        """
        Run specified compliance checks on the image.
        Returns aggregated results.
        """
        if checks is None:
            checks = self.config.get("required_compliance_checks", ["logo_presence", "brand_colors"])
        
        results = {}
        overall_passed = True
        
        for check in checks:
            if check == "logo_presence":
                result = self.check_logo_presence(image_path)
            elif check == "brand_colors":
                result = self.check_brand_colors(image_path)
            else:
                result = {
                    "passed": False,
                    "reason": f"Unknown check: {check}",
                    "details": {}
                }
            
            results[check] = result
            if not result["passed"]:
                overall_passed = False
        
        return {
            "overall_passed": overall_passed,
            "checks": results,
            "image_path": image_path,
            "timestamp": np.datetime64('now').astype(str)
        }


def main():
    """Test the compliance checker with a sample image."""
    if len(sys.argv) < 2:
        print("Usage: python brand_compliance.py <image_path> [config_path]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else "../configs/brand_config.json"
    
    checker = BrandComplianceChecker(config_path)
    results = checker.run_compliance_checks(image_path)
    
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()