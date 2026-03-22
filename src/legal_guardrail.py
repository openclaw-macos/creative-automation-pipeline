#!/usr/bin/env python3
"""
Legal Content Guardrail Module.
Flags prohibited words in campaign messages before they are sent to image overlay or TTS.
"""
import json
import re
import yaml
from typing import List, Dict, Any, Union

class LegalGuardrail:
    def __init__(self, config_path: str = "../configs/brand_config.json"):
        """
        Load prohibited words from configuration.
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.prohibited_words = self.config.get("prohibited_words", [])
        # Convert to lowercase for case-insensitive matching
        self.prohibited_lower = [word.lower() for word in self.prohibited_words]
        
        # Compile regex patterns for whole word matching
        self.patterns = [re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE) for word in self.prohibited_words]
    
    def check_text(self, text: str) -> Dict[str, Any]:
        """
        Check text for prohibited words.
        Returns dict with matches and pass/fail.
        """
        if not text:
            return {
                "passed": True,
                "matches": [],
                "flagged_text": ""
            }
        
        matches = []
        flagged_text = text
        
        # Find matches
        for pattern, word in zip(self.patterns, self.prohibited_words):
            for match in pattern.finditer(text):
                matches.append({
                    "word": word,
                    "start": match.start(),
                    "end": match.end(),
                    "matched_text": match.group()
                })
        
        # Create flagged text with markers
        if matches:
            # Sort matches by start position descending for replacement
            matches_sorted = sorted(matches, key=lambda m: m['start'], reverse=True)
            for match in matches_sorted:
                flagged_text = (
                    flagged_text[:match['start']] +
                    f"[PROHIBITED: {match['word']}]" +
                    flagged_text[match['end']:]
                )
        
        return {
            "passed": len(matches) == 0,
            "matches": matches,
            "flagged_text": flagged_text,
            "prohibited_word_count": len(matches)
        }
    
    def check_campaign_message(self, campaign_message: Union[str, Dict, List]) -> Dict[str, Any]:
        """
        Check campaign message (could be string, JSON, or YAML) for prohibited content.
        """
        if isinstance(campaign_message, str):
            # Try to parse as JSON or YAML
            try:
                data = json.loads(campaign_message)
                return self.check_structure(data)
            except json.JSONDecodeError:
                try:
                    data = yaml.safe_load(campaign_message)
                    return self.check_structure(data)
                except yaml.YAMLError:
                    # Treat as plain text
                    return self.check_text(campaign_message)
        elif isinstance(campaign_message, (dict, list)):
            return self.check_structure(campaign_message)
        else:
            return {
                "passed": False,
                "reason": f"Unsupported message type: {type(campaign_message)}",
                "matches": []
            }
    
    def check_structure(self, data: Any, path: str = "") -> Dict[str, Any]:
        """
        Recursively check all string values in a data structure.
        """
        matches = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                result = self.check_structure(value, new_path)
                matches.extend(result.get("matches", []))
        elif isinstance(data, list):
            for i, value in enumerate(data):
                new_path = f"{path}[{i}]"
                result = self.check_structure(value, new_path)
                matches.extend(result.get("matches", []))
        elif isinstance(data, str):
            result = self.check_text(data)
            for match in result.get("matches", []):
                match["path"] = path
                matches.append(match)
        
        return {
            "passed": len(matches) == 0,
            "matches": matches,
            "total_matches": len(matches)
        }
    
    def filter_campaign_message(self, campaign_message: Union[str, Dict, List]) -> str:
        """
        Return a filtered version of the campaign message with prohibited words replaced.
        """
        if isinstance(campaign_message, str):
            result = self.check_text(campaign_message)
            return result["flagged_text"]
        elif isinstance(campaign_message, (dict, list)):
            # Convert to JSON string, filter, then parse back
            json_str = json.dumps(campaign_message)
            result = self.check_text(json_str)
            filtered = result["flagged_text"]
            try:
                return json.loads(filtered)
            except json.JSONDecodeError:
                return filtered
        else:
            return str(campaign_message)


def main():
    """Test the legal guardrail with sample messages."""
    guardrail = LegalGuardrail()
    
    # Test cases
    test_messages = [
        "Buy our cheap product now! Limited time offer!",
        "Our premium quality product is the best in the market.",
        "{\"headline\": \"Click here to win a prize!\", \"body\": \"Don't miss out!\"}",
        "---\nheadline: Get free samples!\nbody: No scam, guaranteed."
    ]
    
    for msg in test_messages:
        print(f"\nTesting message: {msg[:50]}...")
        result = guardrail.check_campaign_message(msg)
        print(f"  Passed: {result['passed']}")
        if result.get('matches'):
            print(f"  Matches: {result['matches']}")
        if result.get('flagged_text'):
            print(f"  Flagged: {result['flagged_text'][:100]}...")


if __name__ == "__main__":
    main()