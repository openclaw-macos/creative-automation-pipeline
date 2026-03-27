#!/usr/bin/env python3
"""
Localization module for Creative Automation Pipeline.
Handles translation and language mapping based on target region.
Supports free translation APIs with fallback to mock translations.
"""
import os
import sys
import json
import requests
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Unified logging
try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level
except ImportError:
    # Fallback for when run as module
    from .utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level

class Localization:
    """
    Localization service for campaign messages and audio.
    Maps target_region to language codes and provides translation.
    """
    
    # Region to language mapping (based on user requirements)
    REGION_TO_LANGUAGE = {
        "North America (USA/Canada)": "en",  # English
        "USA": "en",  # English (backward compatibility)
        "European Union (Germany/France)": "de",  # German
        "Japan": "ja",  # Japanese
        "UAE / Saudi Arabia": "ar",  # Arabic
        "Brazil": "pt",  # Portuguese
        "Scandinavia (Sweden/Denmark)": "sv",  # Swedish
        # Additional common mappings
        "UK": "en",
        "Canada": "en",
        "Australia": "en",
        "France": "fr",
        "Germany": "de",
        "Spain": "es",
        "Italy": "it",
        "China": "zh",
        "India": "hi",
        "South Korea": "ko",
        "Mexico": "es",
    }
    
    # Language to TTS voice mapping (for Voicebox/Edge TTS)
    LANGUAGE_TO_VOICE = {
        "en": "en-US",  # English US
        "de": "de-DE",  # German
        "ja": "ja-JP",  # Japanese
        "ar": "ar-SA",  # Arabic (Saudi Arabia)
        "pt": "pt-BR",  # Portuguese (Brazil)
        "sv": "sv-SE",  # Swedish
        "fr": "fr-FR",  # French
        "es": "es-ES",  # Spanish
        "it": "it-IT",  # Italian
        "zh": "zh-CN",  # Chinese
        "hi": "hi-IN",  # Hindi
        "ko": "ko-KR",  # Korean
    }
    
    # Common phrases for mock translation (for testing)
    COMMON_PHRASES = {
        "en": {
            "Start your day smarter with our kitchen essentials": "Start your day smarter with our kitchen essentials",
            "Premium quality for modern living": "Premium quality for modern living",
            "Innovative design meets functionality": "Innovative design meets functionality",
        },
        "de": {
            "Start your day smarter with our kitchen essentials": "Starten Sie Ihren Tag klüger mit unseren Küchenessentials",
            "Premium quality for modern living": "Premiumqualität für modernes Leben",
            "Innovative design meets functionality": "Innovatives Design trifft auf Funktionalität",
        },
        "ja": {
            "Start your day smarter with our kitchen essentials": "キッチン必需品でよりスマートな一日を始めましょう",
            "Premium quality for modern living": "モダンな生活のためのプレミアム品質",
            "Innovative design meets functionality": "革新的なデザインと機能性の融合",
            "The science of glow. Achieve crystal-clear skin with precision.": "輝きの科学。精密さでクリスタルクリアな肌を実現。",
        },
        "ar": {
            "Start your day smarter with our kitchen essentials": "ابدأ يومك بذكاء أكبر مع أساسيات مطبخنا",
            "Premium quality for modern living": "جودة ممتازة للحياة العصرية",
            "Innovative design meets functionality": "التصميم المبتكر يلتقي بالوظيفة",
        },
        "pt": {
            "Start your day smarter with our kitchen essentials": "Comece seu dia de forma mais inteligente com nossos utensílios de cozinha",
            "Premium quality for modern living": "Qualidade premium para a vida moderna",
            "Innovative design meets functionality": "Design inovador encontra funcionalidade",
        },
        "sv": {
            "Start your day smarter with our kitchen essentials": "Börja din dag smartare med våra köksbasvaror",
            "Premium quality for modern living": "Premiumkvalitet för modernt liv",
            "Innovative design meets functionality": "Innovativ design möter funktionalitet",
        },
    }
    
    def __init__(self, use_mock: bool = False, translation_api: str = "libre"):
        """
        Initialize localization service.
        
        Args:
            use_mock: Use mock translations instead of API (for testing)
            translation_api: Which translation API to use ("libre", "google", "mymemory")
        """
        self.use_mock = use_mock
        self.translation_api = translation_api
        
        # API endpoints
        self.api_endpoints = {
            "libre": "https://libretranslate.com/translate",
            "google": "https://translate.googleapis.com/translate_a/single",
            "mymemory": "https://api.mymemory.translated.net/get",
        }
    
    def get_language_code(self, target_region: str) -> str:
        """
        Get ISO 639-1 language code for a target region.
        Returns "en" as default if region not found.
        """
        # Try exact match first
        if target_region in self.REGION_TO_LANGUAGE:
            return self.REGION_TO_LANGUAGE[target_region]
        
        # Try partial match (e.g., "European Union" contains "Europe")
        target_lower = target_region.lower()
        for region, lang in self.REGION_TO_LANGUAGE.items():
            if region.lower() in target_lower or target_lower in region.lower():
                return lang
        
        # Default to English
        log_warning(f"Unknown target_region '{target_region}', defaulting to 'en'")
        return "en"
    
    def get_language_from_brief(self, brief: Dict) -> str:
        """
        Get language code from campaign brief.
        Prefers target_language field, falls back to target_region mapping.
        
        Args:
            brief: Campaign brief dictionary
            
        Returns:
            ISO 639-1 language code (e.g., "en", "ja")
        """
        # First try target_language field
        if "target_language" in brief:
            target_lang = brief["target_language"]
            # If it's already a language code (2-3 chars), return it
            if len(target_lang) in (2, 3) and target_lang.isalpha():
                return target_lang.lower()
            # Otherwise try to map it
            return self.get_language_code(target_lang)
        
        # Fall back to target_region
        target_region = brief.get("target_region", "North America (USA/Canada)")
        return self.get_language_code(target_region)
    
    def get_voice_code(self, language_code: str) -> str:
        """
        Get TTS voice code for a language code.
        Returns default voice code if not found.
        """
        return self.LANGUAGE_TO_VOICE.get(language_code, "en-US")
    
    def translate_text(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
        """
        Translate text using selected translation API or mock translation.
        
        Args:
            text: Text to translate
            source_lang: Source language code (default: auto-detect)
            target_lang: Target language code
            
        Returns:
            Translated text (or original if translation fails)
        """
        # Don't translate if source and target are the same
        if source_lang != "auto" and source_lang == target_lang:
            return text
        
        # Use mock translation if enabled
        if self.use_mock:
            return self._mock_translate(text, target_lang)
        
        # Use actual translation API
        try:
            if self.translation_api == "libre":
                # Try LibreTranslate first
                try:
                    return self._translate_libre(text, source_lang, target_lang)
                except Exception as e:
                    log_warning(f"LibreTranslate failed: {e}, trying Google Translate")
                    # Fall back to Google Translate
                    try:
                        return self._translate_google(text, source_lang, target_lang)
                    except Exception as e2:
                        log_warning(f"Google Translate also failed: {e2}, using mock translation")
                        return self._mock_translate(text, target_lang)
            elif self.translation_api == "google":
                return self._translate_google(text, source_lang, target_lang)
            elif self.translation_api == "mymemory":
                return self._translate_mymemory(text, source_lang, target_lang)
            else:
                log_warning(f"Unknown translation API '{self.translation_api}', using mock")
                return self._mock_translate(text, target_lang)
        except Exception as e:
            log_warning(f"Translation failed: {e}, using mock translation")
            return self._mock_translate(text, target_lang)
    
    def _mock_translate(self, text: str, target_lang: str) -> str:
        """
        Mock translation using pre-defined phrases.
        Falls back to original text if phrase not found.
        """
        if target_lang in self.COMMON_PHRASES:
            phrases = self.COMMON_PHRASES[target_lang]
            # Check if exact phrase exists
            if text in phrases:
                return phrases[text]
            
            # Check for partial matches (for longer texts)
            for phrase, translation in phrases.items():
                if phrase in text:
                    # Replace the phrase in the text
                    return text.replace(phrase, translation)
        
        # Return original text if no translation found
        return text
    
    def _translate_libre(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate using LibreTranslate API (free, open source).
        """
        if not text or not text.strip():
            return text
        
        # Prepare request
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text"
        }
        
        try:
            response = requests.post(
                self.api_endpoints["libre"],
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()  # Raise HTTPError for bad status codes
            result = response.json()
            translated = result.get("translatedText", text)
            if translated == text:
                raise ValueError(f"LibreTranslate returned unchanged text for '{text[:50]}...' (likely API failure)")
            if translated != text:
                log_info(f"LibreTranslate successful: '{text[:50]}...' → '{translated[:50]}...'")
            return translated
        except Exception as e:
            log_warning(f"LibreTranslate request failed: {e}")
            return text
    
    def _translate_google(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate using Google Translate API (free tier, limited).
        """
        if not text or not text.strip():
            return text
        
        # URL encode text
        encoded_text = quote(text)
        
        # Build URL
        url = f"{self.api_endpoints['google']}?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={encoded_text}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad status codes
            result = response.json()
            # Google returns nested structure
            if not result or len(result) == 0 or not result[0]:
                raise ValueError("Google Translate returned empty result")
            
            # Extract translation from nested arrays
            translated_parts = []
            for part in result[0]:
                if part and len(part) > 0:
                    translated_parts.append(part[0])
            translated = "".join(translated_parts) if translated_parts else text
            
            if translated == text:
                raise ValueError(f"Google Translate returned unchanged text for '{text[:50]}...'")
            
            log_info(f"Google Translate successful: '{text[:50]}...' → '{translated[:50]}...'")
            return translated
        except Exception as e:
            log_warning(f"Google Translate request failed: {e}")
            return text
    
    def _translate_mymemory(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate using MyMemory Translation API (free).
        """
        if not text or not text.strip():
            return text
        
        # URL encode text
        encoded_text = quote(text)
        
        # Build URL
        url = f"{self.api_endpoints['mymemory']}?q={encoded_text}&langpair={source_lang}|{target_lang}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if "responseData" in result and "translatedText" in result["responseData"]:
                    translated = result["responseData"]["translatedText"]
                    if translated != text:
                        log_info(f"MyMemory Translation successful: '{text[:50]}...' → '{translated[:50]}...'")
                    return translated
            return text
        except Exception as e:
            log_warning(f"MyMemory Translation request failed: {e}")
            return text
    
    def localize_campaign(self, brief: Dict, use_translation: bool = True) -> Dict:
        """
        Localize a campaign brief based on target_language or target_region.
        
        Args:
            brief: Campaign brief dictionary
            use_translation: Whether to translate campaign messages
            
        Returns:
            Localized brief with language_code and translated messages
        """
        # Create copy to avoid modifying original
        localized = brief.copy()
        
        # Get language code (prefers target_language, falls back to target_region)
        language_code = self.get_language_from_brief(brief)
        localized["language_code"] = language_code
        
        # Get voice code for TTS
        voice_code = self.get_voice_code(language_code)
        localized["voice_code"] = voice_code
        
        # Get region and audience for context
        target_region = brief.get("target_region", "North America (USA/Canada)")
        audience = brief.get("audience", "")
        
        # Translate campaign_message if needed
        if use_translation and "campaign_message" in brief:
            original_message = brief["campaign_message"]
            if language_code != "en":  # Only translate if not English
                translated = self.translate_text(original_message, "auto", language_code)
                localized["campaign_message_localized"] = translated
                localized["campaign_message_original"] = original_message
            else:
                localized["campaign_message_localized"] = original_message
                localized["campaign_message_original"] = original_message
        
        # Generate or translate campaign_video_message if not provided
        if "campaign_video_message" not in brief and "campaign_message" in brief:
            # Generate enhanced video message with products, audience, and region
            products = brief.get("products", [])
            product_list = " and ".join(products) if len(products) <= 2 else f"{products[0]} and {len(products)-1} other products"
            
            base_message = brief.get("campaign_message", "")
            enhanced_message = f"{base_message}. These products are well suited for {audience} living in {target_region}"
            
            if language_code != "en":
                enhanced_message = self.translate_text(enhanced_message, "auto", language_code)
            
            localized["campaign_video_message"] = enhanced_message
            localized["campaign_video_message_generated"] = True
        
        # Translate existing campaign_video_message if provided
        elif use_translation and "campaign_video_message" in brief:
            original_video_message = brief["campaign_video_message"]
            if language_code != "en":
                translated = self.translate_text(original_video_message, "auto", language_code)
                localized["campaign_video_message_localized"] = translated
                localized["campaign_video_message_original"] = original_video_message
            else:
                localized["campaign_video_message_localized"] = original_video_message
                localized["campaign_video_message_original"] = original_video_message
        
        return localized


def main():
    """Test localization service."""
    # Test brief
    test_brief = {
        "products": ["Coffee Maker", "Blender"],
        "target_region": "Japan",
        "audience": "Young professionals 25-35",
        "campaign_message": "Start your day smarter with our kitchen essentials"
    }
    
    log_info("Testing Localization Service")
    log_info("============================")
    
    # Create localization service with mock translation
    loc = Localization(use_mock=True)
    
    # Test language code mapping
    regions = ["USA", "European Union (Germany/France)", "Japan", "UAE / Saudi Arabia", "Brazil", "Scandinavia (Sweden/Denmark)"]
    for region in regions:
        lang = loc.get_language_code(region)
        voice = loc.get_voice_code(lang)
        log_info(f"Region: {region:<30} → Language: {lang:<5} → Voice: {voice}")
    
    log_info("")
    
    # Test localization
    localized = loc.localize_campaign(test_brief)
    log_info(f"Original brief: {test_brief}")
    log_info(f"Localized brief: {json.dumps(localized, indent=2, ensure_ascii=False)}")
    
    log_info("")
    
    # Test actual translation (if internet available)
    log_info("Testing actual translation (requires internet):")
    loc_real = Localization(use_mock=False, translation_api="libre")
    test_text = "Hello, world!"
    for target_lang in ["es", "fr", "de"]:
        translated = loc_real.translate_text(test_text, "en", target_lang)
        log_info(f"  '{test_text}' → {target_lang}: '{translated}'")


if __name__ == "__main__":
    main()