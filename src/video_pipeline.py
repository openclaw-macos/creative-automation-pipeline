#!/usr/bin/env python3
"""
Video Pipeline Module for Creative Automation Pipeline.
Extends image generation with video assembly, text/logo overlays, Voicebox narration.
"""
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# Try to import OpenCV for better image processing
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("WARNING: OpenCV not available. Using PIL fallback for video processing.")

class VideoPipeline:
    def __init__(self, brand_config_path: str = "../configs/brand_config.json"):
        """
        Initialize video pipeline with brand configuration.
        """
        self.brand_config_path = brand_config_path
        with open(brand_config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.logo_path = self.config.get("logo_path", "")
        self.text_settings = self.config.get("text_overlay_settings", {})
        self.video_settings = self.config.get("video_settings", {})
        self.logo_settings = self.config.get("logo_check_settings", {})
        
        # Defaults
        self.font_size = self.text_settings.get("font_size", 48)
        self.font_color = self.text_settings.get("font_color", "#FFFFFF")
        self.text_position = self.text_settings.get("position", "bottom-center")
        self.bg_opacity = self.text_settings.get("background_opacity", 0.7)
        self.fade_in_ms = self.text_settings.get("fade_in_ms", 500)
        self.fade_out_ms = self.text_settings.get("fade_out_ms", 500)
        
        self.logo_opacity = self.logo_settings.get("opacity", 0.1)  # 10% default
        self.logo_position = self.logo_settings.get("preferred_position", "top-right")
        
        self.fps = self.video_settings.get("fps", 30)
        self.resolution = self.video_settings.get("resolution", "1920x1080")
        
        # Parse resolution
        if "x" in self.resolution:
            self.video_width, self.video_height = map(int, self.resolution.split("x"))
        else:
            self.video_width, self.video_height = 1920, 1080
    
    def add_text_overlay(self, image_path: str, text: str, output_path: str) -> str:
        """
        Add text overlay to image with background and fade effect markers.
        Returns path to the image with overlay.
        """
        try:
            # Open image
            img = Image.open(image_path).convert("RGBA")
            img_width, img_height = img.size
            
            # Create a temporary image for text
            txt_img = Image.new("RGBA", (img_width, img_height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_img)
            
            # Try to load font
            try:
                # Try system fonts
                font_paths = [
                    "/System/Library/Fonts/Helvetica.ttc",
                    "/System/Library/Fonts/Arial.ttf",
                    "/Library/Fonts/Arial.ttf",
                ]
                font = None
                for fp in font_paths:
                    if os.path.exists(fp):
                        font = ImageFont.truetype(fp, self.font_size)
                        break
                if font is None:
                    font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            
            # Calculate text position
            lines = self._wrap_text(text, font, img_width * 0.8)
            line_height = int(self.font_size * 1.2)
            total_text_height = len(lines) * line_height
            
            # Calculate position based on config
            if self.text_position == "bottom-center":
                x = img_width // 2
                y = img_height - total_text_height - 50
                text_anchor = "mm"  # middle middle
            elif self.text_position == "top-center":
                x = img_width // 2
                y = 50 + total_text_height // 2
                text_anchor = "mm"
            elif self.text_position == "center":
                x = img_width // 2
                y = img_height // 2
                text_anchor = "mm"
            else:  # bottom-center default
                x = img_width // 2
                y = img_height - total_text_height - 50
                text_anchor = "mm"
            
            # Draw text background (semi-transparent rectangle)
            bg_padding = 20
            bg_x1 = x - (img_width * 0.8) // 2 - bg_padding
            bg_y1 = y - total_text_height // 2 - bg_padding
            bg_x2 = x + (img_width * 0.8) // 2 + bg_padding
            bg_y2 = y + total_text_height // 2 + bg_padding
            
            bg_color = (0, 0, 0, int(255 * self.bg_opacity))
            draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=bg_color)
            
            # Draw text lines
            text_color = tuple(int(self.font_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (255,)
            
            for i, line in enumerate(lines):
                line_y = y - total_text_height // 2 + i * line_height + line_height // 2
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_x = x
                
                draw.text((line_x, line_y), line, fill=text_color, font=font, anchor="mm")
            
            # Composite images
            result = Image.alpha_composite(img, txt_img)
            result.save(output_path, "PNG")
            
            return output_path
            
        except Exception as e:
            print(f"ERROR in add_text_overlay: {e}")
            # Return original image if overlay fails
            import shutil
            shutil.copy2(image_path, output_path)
            return output_path
    
    def add_logo_overlay(self, image_path: str, output_path: str) -> str:
        """
        Add logo overlay to image at configured position with opacity.
        Returns path to the image with logo.
        """
        try:
            # Check if logo exists
            logo_path = self.logo_path
            if not os.path.exists(logo_path):
                # Try small logo
                small_logo = logo_path.replace(".png", "_small.png")
                if os.path.exists(small_logo):
                    logo_path = small_logo
                else:
                    print(f"WARNING: Logo not found at {logo_path}")
                    return image_path
            
            # Open images
            img = Image.open(image_path).convert("RGBA")
            logo = Image.open(logo_path).convert("RGBA")
            
            # Resize logo to appropriate size (max 10% of image width)
            max_logo_width = int(img.width * 0.15)  # 15% of image width
            logo_ratio = logo.width / logo.height
            new_logo_width = min(logo.width, max_logo_width)
            new_logo_height = int(new_logo_width / logo_ratio)
            logo = logo.resize((new_logo_width, new_logo_height), Image.Resampling.LANCZOS)
            
            # Apply opacity
            alpha = logo.split()[3]
            alpha = alpha.point(lambda p: int(p * self.logo_opacity))  # 10% opacity
            logo.putalpha(alpha)
            
            # Calculate position
            padding = 20
            if self.logo_position == "top-right":
                x = img.width - logo.width - padding
                y = padding
            elif self.logo_position == "top-left":
                x = padding
                y = padding
            elif self.logo_position == "bottom-right":
                x = img.width - logo.width - padding
                y = img.height - logo.height - padding
            elif self.logo_position == "bottom-left":
                x = padding
                y = img.height - logo.height - padding
            else:  # top-right default
                x = img.width - logo.width - padding
                y = padding
            
            # Composite logo onto image
            img.paste(logo, (x, y), logo)
            img.save(output_path, "PNG")
            
            return output_path
            
        except Exception as e:
            print(f"ERROR in add_logo_overlay: {e}")
            import shutil
            shutil.copy2(image_path, output_path)
            return output_path
    
    def generate_voiceover(self, text: str, output_path: str, 
                          voicebox_url: str = "http://127.0.0.1:17493") -> Optional[str]:
        """
        Generate voiceover using Voicebox TTS.
        Returns path to audio file if successful.
        """
        try:
            # Voicebox API endpoint
            api_url = f"{voicebox_url}/api/tts"
            
            # Prepare request
            payload = {
                "text": text,
                "speaker_id": "default",  # Use default voice
                "language": "en",
                "speed": 1.0
            }
            
            print(f"Generating voiceover with Voicebox at {voicebox_url}...")
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Voiceover saved to {output_path}")
                return output_path
            else:
                print(f"⚠️  Voicebox API error: {response.status_code} - {response.text}")
                # Fallback: create silent audio
                self._create_silent_audio(output_path, duration=5)
                return output_path
                
        except Exception as e:
            print(f"⚠️  Voiceover generation failed: {e}")
            # Fallback: create silent audio
            self._create_silent_audio(output_path, duration=5)
            return output_path
    
    def create_video(self, image_path: str, audio_path: str, output_path: str,
                    duration_seconds: int = 10) -> str:
        """
        Create video from image and audio using FFmpeg.
        Includes fade effects for text.
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Get audio duration if available
            audio_duration = self._get_audio_duration(audio_path)
            if audio_duration > 0:
                duration_seconds = max(audio_duration, 5)  # Minimum 5 seconds
            
            # FFmpeg command to create video with fade effects
            # Center crop if image is not 16:9
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-loop", "1",
                "-i", image_path,
                "-i", audio_path,
                "-vf", self._get_video_filter(duration_seconds),
                "-t", str(duration_seconds),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                output_path
            ]
            
            print(f"Creating video with FFmpeg: {' '.join(cmd[:8])}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Video created: {output_path}")
                return output_path
            else:
                print(f"⚠️  FFmpeg error: {result.stderr}")
                # Try simpler command
                return self._create_simple_video(image_path, audio_path, output_path, duration_seconds)
                
        except Exception as e:
            print(f"ERROR in create_video: {e}")
            # Try fallback
            return self._create_simple_video(image_path, audio_path, output_path, duration_seconds)
    
    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width > max_width:
                if len(current_line) == 1:
                    lines.append(test_line)
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit lines if needed
        max_lines = 3
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1][:40] + "..."
        
        return lines
    
    def _get_video_filter(self, duration: int) -> str:
        """Generate FFmpeg video filter string for fade effects."""
        # Fade in/out for text (using fade filter on entire video)
        fade_in = f"fade=t=in:st=0:d={self.fade_in_ms/1000}"
        fade_out = f"fade=t=out:st={duration - self.fade_out_ms/1000}:d={self.fade_out_ms/1000}"
        
        # Scale and crop to target resolution
        scale_crop = f"scale={self.video_width}:{self.video_height}:force_original_aspect_ratio=increase,crop={self.video_width}:{self.video_height}"
        
        return f"{scale_crop},{fade_in},{fade_out}"
    
    def _create_silent_audio(self, output_path: str, duration: int = 5) -> str:
        """Create silent audio as fallback."""
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration),
            "-c:a", "libmp3lame",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio file duration using FFprobe."""
        if not os.path.exists(audio_path):
            return 0
        
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip()) if result.returncode == 0 else 0
        except:
            return 0
    
    def _create_simple_video(self, image_path: str, audio_path: str, 
                           output_path: str, duration: int) -> str:
        """Create simple video without complex filters as fallback."""
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-vf", f"scale={self.video_width}:{self.video_height}:force_original_aspect_ratio=increase,crop={self.video_width}:{self.video_height}",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        return output_path if os.path.exists(output_path) else ""

def main():
    """Test the video pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test video pipeline")
    parser.add_argument("--image", required=True, help="Input image path")
    parser.add_argument("--text", required=True, help="Text for overlay")
    parser.add_argument("--output-dir", default="./outputs/video", help="Output directory")
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = VideoPipeline()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Add text overlay
    text_overlay_path = os.path.join(args.output_dir, "text_overlay.png")
    pipeline.add_text_overlay(args.image, args.text, text_overlay_path)
    
    # Add logo overlay
    final_image_path = os.path.join(args.output_dir, "final_overlay.png")
    pipeline.add_logo_overlay(text_overlay_path, final_image_path)
    
    # Generate voiceover
    audio_path = os.path.join(args.output_dir, "voiceover.mp3")
    pipeline.generate_voiceover(args.text, audio_path)
    
    # Create video
    video_path = os.path.join(args.output_dir, "final_video.mp4")
    pipeline.create_video(final_image_path, audio_path, video_path)
    
    print(f"\n✅ Video pipeline completed!")
    print(f"   Text overlay: {text_overlay_path}")
    print(f"   Final image: {final_image_path}")
    print(f"   Voiceover: {audio_path}")
    print(f"   Video: {video_path}")

if __name__ == "__main__":
    main()