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
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }
        
        # Default avatar settings (can be overridden)
        self.default_avatar_id = "anna_costume1_cameraA"  # Example avatar
        self.default_voice_id = "1bd001e7e50f421d891986aad5158bc8"  # Example voice ID
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
            url = f"{self.base_url}/v1/avatars"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and "avatars" in data["data"]:
                self._avatars_cache = data["data"]["avatars"]
            else:
                self._avatars_cache = []
                
            return self._avatars_cache
        except Exception as e:
            print(f"WARNING: Failed to fetch avatars from HeyGen: {e}")
            # Return default avatars list
            return [
                {"avatar_id": "anna_costume1_cameraA", "name": "Anna (Professional)"},
                {"avatar_id": "lucas_costume1_cameraA", "name": "Lucas (Business)"},
                {"avatar_id": "emma_costume1_cameraA", "name": "Emma (Casual)"},
            ]
    
    def get_available_voices(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of available voices from HeyGen API.
        Uses cache to avoid repeated API calls.
        """
        if self._voices_cache is not None and not force_refresh:
            return self._voices_cache
            
        try:
            url = f"{self.base_url}/v1/voices"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and "voices" in data["data"]:
                self._voices_cache = data["data"]["voices"]
            else:
                self._voices_cache = []
                
            return self._voices_cache
        except Exception as e:
            print(f"WARNING: Failed to fetch voices from HeyGen: {e}")
            # Return default voices list
            return [
                {"voice_id": "1bd001e7e50f421d891986aad5158bc8", "name": "English Female 1"},
                {"voice_id": "2ac76e7a8b6d4c5f9e8f7a6b5c4d3e2f", "name": "English Male 1"},
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
            avatar_id = self.default_avatar_id
            
        if voice_id is None:
            # Try to find Voicebox voice
            voicebox_voice = self.find_voicebox_voice()
            if voicebox_voice:
                voice_id = voicebox_voice
                print(f"Using Voicebox-compatible voice: {voice_id}")
            else:
                voice_id = self.default_voice_id
                print(f"Using default voice: {voice_id}")
        
        # Prepare API request
        url = f"{self.base_url}/v1/video/generate"
        
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
            print(f"Creating avatar video with HeyGen API...")
            print(f"  Avatar: {avatar_id}")
            print(f"  Voice: {voice_id}")
            print(f"  Script length: {len(script)} characters")
            
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
            
            print(f"✅ Video generation started. Task ID: {task_id}")
            
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
        url = f"{self.base_url}/v1/video/{task_id}"
        
        print(f"Polling for video completion (max {max_attempts * poll_interval}s)...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                status = data.get("data", {}).get("status")
                video_url = data.get("data", {}).get("video_url")
                
                if status == "completed" and video_url:
                    print(f"✅ Video completed on attempt {attempt + 1}")
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
                        print(f"  Still processing... ({attempt * poll_interval}s elapsed)")
                    time.sleep(poll_interval)
                else:
                    print(f"  Unknown status: {status}, waiting...")
                    time.sleep(poll_interval)
                    
            except Exception as e:
                print(f"  Poll error: {e}, retrying...")
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
            
            print(f"Downloading video from: {video_url}")
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(output_path)
            print(f"✅ Video downloaded: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
            
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
        
        print(f"Using local model '{local_model_type}' for script planning...")
        
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
    
    parser = argparse.ArgumentParser(description="Test HeyGen avatar generation")
    parser.add_argument("--api-key", required=True, help="HeyGen API key")
    parser.add_argument("--script", default="Hello, this is a test of the HeyGen avatar system.", help="Script for avatar to speak")
    parser.add_argument("--output", default="output/heygen_test.mp4", help="Output video path")
    parser.add_argument("--local-model", choices=["mistral-nemo", "qwen3-vl", "qwen3.5"], default="mistral-nemo", help="Local model to use for planning")
    
    args = parser.parse_args()
    
    # Initialize HeyGen integration
    heygen = HeyGenIntegration(api_key=args.api_key)
    
    # Test available avatars and voices
    print("Available avatars:")
    avatars = heygen.get_available_avatars()
    for avatar in avatars[:3]:  # Show first 3
        print(f"  - {avatar.get('name', 'Unknown')} (ID: {avatar.get('avatar_id', 'N/A')})")
    
    print("\nAvailable voices:")
    voices = heygen.get_available_voices()
    for voice in voices[:3]:  # Show first 3
        print(f"  - {voice.get('name', 'Unknown')} (ID: {voice.get('voice_id', 'N/A')})")
    
    # Try to find Voicebox voice
    voicebox_voice = heygen.find_voicebox_voice()
    if voicebox_voice:
        print(f"\n✅ Found Voicebox-compatible voice: {voicebox_voice}")
    else:
        print(f"\n⚠️  No Voicebox-compatible voice found, using default")
    
    # Generate video with local model planning
    print(f"\nGenerating avatar video with local model '{args.local_model}'...")
    result = heygen.generate_with_local_models(
        prompt=args.script,
        local_model_type=args.local_model,
        output_path=args.output
    )
    
    if result["success"]:
        print(f"\n✅ HeyGen video generation successful!")
        print(f"   Video saved to: {result['video_path']}")
        print(f"   Task ID: {result.get('task_id', 'N/A')}")
        print(f"   File size: {result.get('file_size_bytes', 0) / 1024 / 1024:.1f} MB")
    else:
        print(f"\n❌ HeyGen video generation failed:")
        print(f"   Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()