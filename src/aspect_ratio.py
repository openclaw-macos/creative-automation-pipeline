#!/usr/bin/env python3
"""
Aspect ratio handling for Creative Automation Pipeline.
Generates multiple aspect ratios from base images.
"""
import os
import sys
from PIL import Image
from typing import List, Tuple, Dict

# Standard aspect ratios for social media
ASPECT_RATIOS = {
    "1_1": (1, 1),      # Square (Instagram, Facebook)
    "16_9": (16, 9),    # Widescreen (YouTube, video)
    "9_16": (9, 16)     # Portrait (Instagram Reels, TikTok)
}

# Common dimensions for each aspect ratio (preserving quality)
DIMENSIONS = {
    "1_1": (1080, 1080),    # Instagram square
    "16_9": (1920, 1080),   # Full HD
    "9_16": (1080, 1920),   # Portrait HD
}

def resize_to_aspect_ratio(image_path: str, output_path: str, 
                          target_width: int, target_height: int,
                          method: str = "center_crop") -> str:
    """
    Resize image to target dimensions using specified method.
    
    Args:
        image_path: Path to source image
        output_path: Path to save resized image
        target_width: Target width
        target_height: Target height
        method: "center_crop", "letterbox", or "stretch"
        
    Returns:
        Path to saved image
    """
    try:
        img = Image.open(image_path).convert("RGB")
        original_width, original_height = img.size
        
        if method == "center_crop":
            # Crop from center to match target aspect ratio
            target_ratio = target_width / target_height
            original_ratio = original_width / original_height
            
            if original_ratio > target_ratio:
                # Image is wider than target, crop width
                new_width = int(original_height * target_ratio)
                left = (original_width - new_width) // 2
                img = img.crop((left, 0, left + new_width, original_height))
            else:
                # Image is taller than target, crop height
                new_height = int(original_width / target_ratio)
                top = (original_height - new_height) // 2
                img = img.crop((0, top, original_width, top + new_height))
                
            # Resize to target dimensions
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
        elif method == "letterbox":
            # Add letterbox/pillarbox to maintain aspect ratio
            target_ratio = target_width / target_height
            original_ratio = original_width / original_height
            
            if original_ratio > target_ratio:
                # Image is wider, add pillarbox (vertical bars)
                new_height = int(original_width / target_ratio)
                if new_height > original_height:
                    # Need to resize first
                    scale = new_height / original_height
                    new_width = int(original_width * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    original_width, original_height = img.size
                
                # Create new image with target dimensions
                new_img = Image.new("RGB", (target_width, target_height), (0, 0, 0))
                x_offset = (target_width - original_width) // 2
                new_img.paste(img, (x_offset, 0))
                img = new_img
            else:
                # Image is taller, add letterbox (horizontal bars)
                new_width = int(original_height * target_ratio)
                if new_width > original_width:
                    scale = new_width / original_width
                    new_height = int(original_height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    original_width, original_height = img.size
                
                # Create new image with target dimensions
                new_img = Image.new("RGB", (target_width, target_height), (0, 0, 0))
                y_offset = (target_height - original_height) // 2
                new_img.paste(img, (0, y_offset))
                img = new_img
                
        else:  # stretch
            # Simply resize (distorts aspect ratio)
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save image
        img.save(output_path, "PNG")
        return output_path
        
    except Exception as e:
        print(f"ERROR resizing {image_path}: {e}")
        return ""

def generate_aspect_ratios(base_image_path: str, output_dir: str, 
                          product_name: str, method: str = "center_crop") -> Dict[str, str]:
    """
    Generate multiple aspect ratios from a base image.
    
    Args:
        base_image_path: Path to base image
        output_dir: Directory to save aspect ratio variants
        product_name: Product name for filename
        method: Resizing method
        
    Returns:
        Dictionary mapping aspect ratio names to file paths
    """
    results = {}
    
    for ratio_name, (width, height) in DIMENSIONS.items():
        # Clean product name for filename
        clean_name = product_name.lower().replace(" ", "_")
        
        # Generate output path
        output_path = os.path.join(output_dir, f"{clean_name}_{ratio_name}.png")
        
        # Resize image
        result = resize_to_aspect_ratio(
            base_image_path, output_path, width, height, method
        )
        
        if result:
            results[ratio_name] = result
            print(f"✅ Generated {ratio_name} ({width}x{height}): {output_path}")
        else:
            print(f"❌ Failed to generate {ratio_name} for {product_name}")
    
    return results

def add_logo_to_image(image_path: str, logo_path: str, output_path: str,
                     position: str = "top-right", opacity: float = 0.1) -> str:
    """
    Add logo overlay to image.
    
    Args:
        image_path: Path to base image
        logo_path: Path to logo image (should be PNG with transparency)
        output_path: Path to save output
        position: "top-right", "top-left", "bottom-right", "bottom-left"
        opacity: Logo opacity (0.0 to 1.0)
        
    Returns:
        Path to saved image
    """
    try:
        if not os.path.exists(logo_path):
            print(f"WARNING: Logo not found at {logo_path}")
            return image_path
        
        # Open images
        img = Image.open(image_path).convert("RGBA")
        logo = Image.open(logo_path).convert("RGBA")
        
        # Resize logo to appropriate size (max 15% of image width)
        max_logo_width = int(img.width * 0.15)
        logo_ratio = logo.width / logo.height
        new_logo_width = min(logo.width, max_logo_width)
        new_logo_height = int(new_logo_width / logo_ratio)
        logo = logo.resize((new_logo_width, new_logo_height), Image.Resampling.LANCZOS)
        
        # Apply opacity
        alpha = logo.split()[3]
        alpha = alpha.point(lambda p: int(p * opacity))
        logo.putalpha(alpha)
        
        # Calculate position
        padding = 20
        if position == "top-right":
            x = img.width - logo.width - padding
            y = padding
        elif position == "top-left":
            x = padding
            y = padding
        elif position == "bottom-right":
            x = img.width - logo.width - padding
            y = img.height - logo.height - padding
        elif position == "bottom-left":
            x = padding
            y = img.height - logo.height - padding
        else:  # top-right default
            x = img.width - logo.width - padding
            y = padding
        
        # Composite logo onto image
        img.paste(logo, (x, y), logo)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save image
        img.save(output_path, "PNG")
        return output_path
        
    except Exception as e:
        print(f"ERROR adding logo to {image_path}: {e}")
        return image_path

def main():
    """Test aspect ratio generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test aspect ratio generation")
    parser.add_argument("--image", required=True, help="Input image path")
    parser.add_argument("--output-dir", default="./outputs/aspect_ratios", help="Output directory")
    parser.add_argument("--product", default="test_product", help="Product name")
    parser.add_argument("--method", default="center_crop", choices=["center_crop", "letterbox", "stretch"],
                       help="Resizing method")
    parser.add_argument("--logo", help="Path to logo for overlay")
    
    args = parser.parse_args()
    
    print("=== Testing Aspect Ratio Generation ===")
    print(f"Input: {args.image}")
    print(f"Output: {args.output_dir}")
    print(f"Method: {args.method}")
    print()
    
    # Generate aspect ratios
    results = generate_aspect_ratios(
        args.image, args.output_dir, args.product, args.method
    )
    
    print(f"\nGenerated {len(results)} aspect ratios")
    
    # Add logo if provided
    if args.logo:
        print(f"\nAdding logo: {args.logo}")
        for ratio_name, image_path in results.items():
            output_with_logo = image_path.replace(".png", "_with_logo.png")
            result = add_logo_to_image(image_path, args.logo, output_with_logo)
            if result:
                print(f"✅ Added logo to {ratio_name}: {output_with_logo}")

if __name__ == "__main__":
    main()