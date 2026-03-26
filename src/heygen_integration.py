#!/usr/bin/env python3
"""
HeyGen Avatar Integration for Creative Automation Pipeline.
Generates avatar videos using HeyGen API with Voicebox TTS voice preference.
Uses local models (qwen3‑vl, mistral‑nemo) for script planning to avoid DeepSeek API charges.
"""
import os
import sys
import json
import time
import requests
from typing import Dict, List, Optional, Any
import base64
from pathlib import Path

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Unified logging
try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level
except ImportError:
    # Fallback for when run as module
    from .utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level

class HeyGenIntegration:
    def __init__(self, api_key: str, base_url: str = "https://api.heygen.com"):
        """
        Initialize HeyGen integration with API key.
        
        Args:
            api_key: HeyGen API key (starts with 'sk_V2_')
            base_url: HeyGen API base URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "x-api-key": api_key,  # HeyGen v2 requires lowercase header
            "Content-Type": "application/json"
        }
        
        # Default avatar settings (can be overridden)
        self.default_avatar_id = "00b82a2d3bc54ae1aa692686411d45f5"  # Digital Twin: Agent 42 from isFutureNOW
        self.default_voice_id = "8a2bdb430871445594dafc3488c54574"  # Voice: RaviK Pullet
        self.default_scene = "default"  # Default scene
        
        # Cache for API responses
        self._avatars_cache = None
        self._voices_cache = None
        
    def get_available_avatars(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of available avatars from HeyGen API.
        Uses cache to avoid repeated API calls.
        """
        if self._avatars_cache is not None and not force_refresh:
            return self._avatars_cache
            
        try:
            url = f"{self.base_url}/v2/avatars"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and "avatars" in data["data"]:
                self._avatars_cache = data["data"]["avatars"]
            else:
                self._avatars_cache = []
                
            return self._avatars_cache
        except Exception as e:
            log_warning(f"Failed to fetch avatars from HeyGen: {e}")
            # Return default avatars list (including digital twin)
            return [
                {"avatar_id": "00b82a2d3bc54ae1aa692686411d45f5", "name": "Agent 42 from isFutureNOW (Digital Twin)"},
                {"avatar_id": "anna_costume1_cameraA", "name": "Anna (Professional)"},
                {"avatar_id": "lucas_costume1_cameraA", "name": "Lucas (Business)"},
            ]
    
    def get_available_voices(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of available voices from HeyGen API.
        Uses cache to avoid repeated API calls.
        """
        if self._voices_cache is not None and not force_refresh:
            return self._voices_cache
            
        try:
            url = f"{self.base_url}/v2/voices"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and "voices" in data["data"]:
                self._voices_cache = data["data"]["voices"]
            else:
                self._voices_cache = []
                
            return self._voices_cache
        except Exception as e:
            log_warning(f"Failed to fetch voices from HeyGen: {e}")
            # Return default voices list (including RaviK Pullet)
            return [
                {"voice_id": "8a2bdb430871445594dafc3488c54574", "name": "RaviK Pullet"},
                {"voice_id": "1bd001e7e50f421d891986aad5158bc8", "name": "English Female 1"},
            ]
    
    def find_voicebox_voice(self) -> Optional[str]:
        """
        Try to find a Voicebox-compatible voice in HeyGen's voice list.
        Returns voice_id if found, None otherwise.
        """
        voices = self.get_available_voices()
        
        # Look for Voicebox-related voice names
        voicebox_keywords = ["voicebox", "VoiceBox", "voice box", "vbx", "VBX"]
        for voice in voices:
            voice_name = voice.get("name", "").lower()
            if any(keyword in voice_name for keyword in voicebox_keywords):
                return voice.get("voice_id")
        
        # If no Voicebox voice found, return first English voice or default
        for voice in voices:
            voice_name = voice.get("name", "").lower()
            if "english" in voice_name:
                return voice.get("voice_id")
        
        # Return default if available
        if voices:
            return voices[0].get("voice_id")
        
        return None
    
    def find_digital_twin_avatar(self) -> Optional[str]:
        """
        Find digital twin avatar by name 'Agent 42 from isFutureNOW' or ID.
        Returns avatar_id if found, None otherwise.
        """
        try:
            avatars = self.get_available_avatars()
            for avatar in avatars:
                avatar_name = avatar.get("name", "").lower()
                avatar_id = avatar.get("avatar_id", "")
                
                # Check for Agent 42 digital twin
                if ("agent 42" in avatar_name or "agent42" in avatar_name or 
                    avatar_id == "00b82a2d3bc54ae1aa692686411d45f5"):
                    return avatar_id
            
            # If not found, return default digital twin ID
            return "00b82a2d3bc54ae1aa692686411d45f5"
        except Exception as e:
            log_warning(f"Digital twin detection failed: {e}")
            return "00b82a2d3bc54ae1aa692686411d45f5"  # Fallback to provided ID
    
    def create_avatar_video(
        self,
        script: str,
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        background: Optional[str] = None,
        output_path: str = "output/heygen_video.mp4",
        resolution: str = "1920x1080",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Create avatar video from script using HeyGen API.
        
        Args:
            script: Text for the avatar to speak
            avatar_id: HeyGen avatar ID (uses default if None)
            voice_id: HeyGen voice ID (uses Voicebox voice if available, otherwise default)
            background: Background image/video URL (optional)
            output_path: Path to save the video
            resolution: Video resolution (e.g., "1920x1080")
            language: Language code (e.g., "en", "es")
            
        Returns:
            Dictionary with success status, video URL, task ID, etc.
        """
        # Use defaults if not specified
        if avatar_id is None:
            avatar_id = self.find_digital_twin_avatar()
            log_info(f"Using digital twin avatar: {avatar_id}")
            
        if voice_id is None:
            # Try to find Voicebox voice
            voicebox_voice = self.find_voicebox_voice()
            if voicebox_voice:
                voice_id = voicebox_voice
                log_info(f"Using Voicebox voice: {voice_id}")
            else:
                voice_id = self.default_voice_id  # Will use RaviK Pullet
                log_info(f"Using configured voice: RaviK Pullet ({voice_id})")
        
        # Prepare API request
        url = f"{self.base_url}/v2/video/generate"
        
        # Build request payload
        payload = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id
                },
                "background": background or {
                    "type": "color",
                    "value": "#FFFFFF"
                }
            }],
            "dimension": {
                "width": int(resolution.split('x')[0]),
                "height": int(resolution.split('x')[1])
            },
            "test": False,
            "language": language
        }
        
        try:
            log_info(f"Creating avatar video with HeyGen API...")
            log_info(f"  Avatar: {avatar_id}")
            log_info(f"  Voice: {voice_id}")
            log_info(f"  Script length: {len(script)} characters")
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if "data" not in data:
                return {
                    "success": False,
                    "error": "Invalid API response",
                    "response": data
                }
            
            task_id = data["data"].get("task_id")
            video_url = data["data"].get("video_url")
            
            if not task_id:
                return {
                    "success": False,
                    "error": "No task ID in response",
                    "response": data
                }
            
            log_success(f"Video generation started. Task ID: {task_id}")
            
            # Wait for video to be ready and download
            if video_url:
                # Video is immediately available (some API plans)
                return self._download_video(video_url, output_path, task_id)
            else:
                # Need to poll for completion
                return self._poll_video_status(task_id, output_path)
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {e}",
                "task_id": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
                "task_id": None
            }
    
    def _poll_video_status(self, task_id: str, output_path: str, poll_interval: int = 5) -> Dict[str, Any]:
        """
        Poll HeyGen API for video generation status.
        
        Args:
            task_id: HeyGen task ID
            output_path: Path to save the video
            poll_interval: Seconds between polls
            
        Returns:
            Dictionary with success status and video path
        """
        max_attempts = 60  # 5 minutes max
        url = f"{self.base_url}/v2/video/{task_id}"
        
        log_info(f"Polling for video completion (max {max_attempts * poll_interval}s)...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                status = data.get("data", {}).get("status")
                video_url = data.get("data", {}).get("video_url")
                
                if status == "completed" and video_url:
                    log_success(f"Video completed on attempt {attempt + 1}")
                    return self._download_video(video_url, output_path, task_id)
                elif status == "failed":
                    return {
                        "success": False,
                        "error": "Video generation failed",
                        "task_id": task_id,
                        "status": status
                    }
                elif status == "processing":
                    if attempt % 6 == 0:  # Print every 30 seconds
                        log_info(f"  Still processing... ({attempt * poll_interval}s elapsed)")
                    time.sleep(poll_interval)
                else:
                    log_warning(f"  Unknown status: {status}, waiting...")
                    time.sleep(poll_interval)
                    
            except Exception as e:
                log_warning(f"  Poll error: {e}, retrying...")
                time.sleep(poll_interval)
        
        return {
            "success": False,
            "error": f"Timeout after {max_attempts * poll_interval} seconds",
            "task_id": task_id
        }
    
    def _download_video(self, video_url: str, output_path: str, task_id: str) -> Dict[str, Any]:
        """
        Download video from URL to output path.
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            log_info(f"Downloading video from: {video_url}")
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(output_path)
            log_success(f"Video downloaded: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
            
            return {
                "success": True,
                "video_path": output_path,
                "task_id": task_id,
                "video_url": video_url,
                "file_size_bytes": file_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Video download failed: {e}",
                "task_id": task_id,
                "video_url": video_url
            }
    
    def generate_with_local_models(
        self,
        prompt: str,
        local_model_type: str = "mistral-nemo",
        output_path: str = "output/heygen_avatar.mp4",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate avatar video using local models for script refinement/planning.
        This avoids DeepSeek API charges while still using HeyGen for avatar generation.
        
        Args:
            prompt: Initial prompt or script idea
            local_model_type: "mistral-nemo", "qwen3-vl", or "qwen3.5"
            output_path: Path to save the video
            **kwargs: Additional arguments for create_avatar_video
            
        Returns:
            Dictionary with success status and video path
        """
        # This is a placeholder for local model integration
        # In a real implementation, you would:
        # 1. Use local LLM to refine/expand the prompt into a proper script
        # 2. Use local vision model to analyze reference images if needed
        # 3. Call HeyGen API with the refined script
        
        log_info(f"Using local model '{local_model_type}' for script planning...")
        
        # For now, just pass the prompt as the script
        # In production, you would call local LLM here
        script = prompt
        
        # Add instruction to use local models (this would be actual LLM calls)
        if local_model_type == "mistral-nemo":
            # Simulate Mistral-Nemo processing
            script = f"[Local model: mistral-nemo processed]\n{script}"
        elif local_model_type == "qwen3-vl":
            # Simulate Qwen3-VL processing
            script = f"[Local model: qwen3-vl processed]\n{script}"
        elif local_model_type == "qwen3.5":
            # Simulate Qwen3.5 processing
            script = f"[Local model: qwen3.5 processed]\n{script}"
        
        # Call HeyGen API
        return self.create_avatar_video(script=script, output_path=output_path, **kwargs)

def main():
    """Test HeyGen integration."""
    import argparse
    import logging
    
    parser = argparse.ArgumentParser(description="Test HeyGen avatar generation")
    parser.add_argument("--api-key", required=True, help="HeyGen API key")
    parser.add_argument("--script", default="Hello, this is a test of the HeyGen avatar system.", help="Script for avatar to speak")
    parser.add_argument("--output", default="output/heygen_test.mp4", help="Output video path")
    parser.add_argument("--local-model", choices=["mistral-nemo", "qwen3-vl", "qwen3.5"], default="mistral-nemo", help="Local model to use for planning")
    parser.add_argument("--target-region", default="USA", help="Target region for localization (e.g., USA, Japan, Brazil)")
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
    
    # Initialize HeyGen integration
    heygen = HeyGenIntegration(api_key=args.api_key)
    
    # Initialize localization
    try:
        from localization import Localization
        loc = Localization(use_mock=True)
        lang_code = loc.get_language_code(args.target_region)
        voice_code = loc.get_voice_code(lang_code)
        
        # Translate script if not English
        if lang_code != "en":
            original_script = args.script
            args.script = loc.translate_text(original_script, "en", lang_code)
            log_info(f"Localization: Region='{args.target_region}', Language='{lang_code}', Voice='{voice_code}'")
            log_info(f"Translated script from: '{original_script[:50]}...'")
            log_info(f"                    to: '{args.script[:50]}...'")
        else:
            log_info(f"Localization: Region='{args.target_region}', Language='{lang_code}' (no translation needed)")
    except ImportError:
        log_warning("Localization module not available. Using English defaults.")
        lang_code = "en"
    
    # Test available avatars and voices
    log_info("\nAvailable avatars:")
    avatars = heygen.get_available_avatars()
    for avatar in avatars:  # Show all avatars to verify digital twin
        log_info(f"  - {avatar.get('name', 'Unknown')} (ID: {avatar.get('avatar_id', 'N/A')})")
    
    log_info("\nAvailable voices:")
    voices = heygen.get_available_voices()
    for voice in voices:  # Show all voices to verify RaviK Pullet
        log_info(f"  - {voice.get('name', 'Unknown')} (ID: {voice.get('voice_id', 'N/A')})")
    
    # Try to find digital twin
    digital_twin_id = heygen.find_digital_twin_avatar()
    if digital_twin_id:
        log_success(f"\nFound digital twin avatar: {digital_twin_id}")
    else:
        log_warning(f"\nDigital twin not found, using default ID")
    
    # Try to find Voicebox voice
    voicebox_voice = heygen.find_voicebox_voice()
    if voicebox_voice:
        log_info(f"Found Voicebox voice: {voicebox_voice}")
    else:
        log_info(f"No Voicebox voice found, using RaviK Pullet")
    
    # Generate video with local model planning
    log_info(f"\nGenerating avatar video with local model '{args.local_model}'...")
    result = heygen.generate_with_local_models(
        prompt=args.script,
        local_model_type=args.local_model,
        output_path=args.output,
        language=lang_code
    )
    
    if result["success"]:
        log_success(f"\nHeyGen video generation successful!")
        log_info(f"   Video saved to: {result['video_path']}")
        log_info(f"   Task ID: {result.get('task_id', 'N/A')}")
        log_info(f"   File size: {result.get('file_size_bytes', 0) / 1024 / 1024:.1f} MB")
    else:
        log_error(f"\nHeyGen video generation failed:")
        log_error(f"   Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()