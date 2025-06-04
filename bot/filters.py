"""AI-powered message filtering for co-parenting topics with detailed moderation."""

from __future__ import annotations

import json
import logging
from typing import Dict, Optional

import openai
from openai import OpenAI

from config import config

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client: Optional[OpenAI] = None

try:
    client = OpenAI(api_key=config.OPENAI_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")


class ModerationResponse:
    """Response from message classification with detailed reasoning."""
    
    def __init__(self, allow: bool, reason: str, category: str = ""):
        self.allow = allow
        self.reason = reason
        self.category = category
    
    def to_dict(self) -> Dict[str, str | bool]:
        return {
            "allow": self.allow,
            "reason": self.reason,
            "category": self.category
        }
    
    @classmethod
    def from_json(cls, json_str: str) -> "ModerationResponse":
        """Create ModerationResponse from JSON string."""
        try:
            data = json.loads(json_str)
            return cls(
                allow=data.get("allow", False),
                reason=data.get("reason", "No reason provided"),
                category=data.get("category", "")
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse moderation response: {e}")
            # Default to blocking with generic message
            return cls(
                allow=False,
                reason="Message could not be properly evaluated",
                category="parsing_error"
            )


def _build_system_prompt() -> str:
    """Build system prompt based on current moderation profile."""
    profile = config.get_moderation_profile()
    
    base_prompt = """You are a co-parenting message moderator. Your job is to evaluate messages for appropriateness in a co-parenting logistics group.

CORE RULES:
1. ALLOW messages about: children's health, education, scheduling, logistics, emergencies
2. BE PERMISSIVE: When in doubt or if context is unclear, ALLOW the message
3. Only BLOCK messages that are OBVIOUSLY inappropriate

RESPONSE FORMAT: Return ONLY valid JSON in this exact format:
{"allow": true/false, "reason": "specific explanation", "category": "reason_category"}

"""
    
    if profile["behaviors"]:
        behavior_text = "\n".join(f"- {behavior}" for behavior in profile["behaviors"])
        
        profile_prompt = f"""
MODERATION PROFILE: {profile["name"]}
Watch specifically for these behavioral patterns:
{behavior_text}

When blocking, use specific language about what pattern was detected.
Examples of targeted responses:
- "This appears to be performative posturing rather than actionable co-parenting communication"
- "This message deflects from logistics to emotional manipulation"
- "This seems designed to craft a narrative rather than address children's needs"
- "This appears to be grandstanding without substance about children's welfare"

"""
        base_prompt += profile_prompt
    
    base_prompt += """
EXAMPLES:
{"allow": true, "reason": "Legitimate scheduling discussion", "category": "scheduling"}
{"allow": false, "reason": "This appears to be performative posturing rather than actionable co-parenting communication", "category": "performative"}
{"allow": true, "reason": "Unclear context but potentially legitimate", "category": "permissive"}

Remember: When message intent is unclear or ambiguous, ALWAYS err on the side of allowing it."""
    
    return base_prompt


def classify(text: str) -> ModerationResponse:
    """
    Classify a message with detailed reasoning.
    
    This function serves as the main interface for message classification.
    To swap in a different LLM provider, modify this function only.
    
    Args:
        text: The message text to classify
        
    Returns:
        ModerationResponse with allow/block decision and specific reasoning
    """
    try:
        return _classify_with_openai(text)
    except Exception as e:
        logger.error(f"Classification failed for text '{text[:50]}...': {e}")
        # Default to allowing on error in permissive mode
        profile = config.get_moderation_profile()
        if profile.get("permissive_mode", True):
            return ModerationResponse(
                allow=True,
                reason="Unable to evaluate - allowing due to permissive mode",
                category="error_permissive"
            )
        else:
            return ModerationResponse(
                allow=False,
                reason="Unable to evaluate message properly",
                category="error_blocking"
            )


def _classify_with_openai(text: str) -> ModerationResponse:
    """
    Classify message using OpenAI GPT-4o with detailed response.
    
    Args:
        text: The message text to classify
        
    Returns:
        ModerationResponse with detailed reasoning
        
    Raises:
        RuntimeError: If OpenAI API call fails
    """
    if not client:
        raise RuntimeError("OpenAI client not initialized")
    
    try:
        system_prompt = _build_system_prompt()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Evaluate this message: {text}"}
            ],
            max_tokens=150,  # Increased for detailed responses
            temperature=0.1,  # Low but not zero for some variation
            timeout=15.0  # Increased timeout for more complex processing
        )
        
        result = response.choices[0].message.content.strip()
        
        # Try to parse as JSON response
        return ModerationResponse.from_json(result)
            
    except openai.RateLimitError:
        logger.error("OpenAI rate limit exceeded")
        raise RuntimeError("AI service temporarily unavailable (rate limit)")
    except openai.APIConnectionError:
        logger.error("OpenAI API connection failed")
        raise RuntimeError("AI service connection failed")
    except openai.APITimeoutError:
        logger.error("OpenAI API timeout")
        raise RuntimeError("AI service timeout")
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise RuntimeError(f"AI service error: {e}")


# Alternative implementation examples for different providers:

def _classify_with_http_api(text: str, api_url: str, api_key: str) -> ModerationResponse:
    """
    Example implementation for generic HTTP API providers.
    
    To use this instead of OpenAI, replace the classify() function body with:
    return _classify_with_http_api(text, "https://api.provider.com/classify", "your_key")
    """
    import requests
    
    try:
        system_prompt = _build_system_prompt()
        
        response = requests.post(
            api_url,
            json={
                "text": text,
                "system_prompt": system_prompt,
                "task": "detailed_coparenting_filter"
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=15.0
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Expect the API to return JSON in our format
        return ModerationResponse.from_json(json.dumps(result))
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP API error: {e}")
        raise RuntimeError(f"AI service error: {e}")


def _classify_with_together_ai(text: str, api_key: str) -> ModerationResponse:
    """
    Example implementation for Together AI with JSON response parsing.
    
    Replace classify() function body with:
    return _classify_with_together_ai(text, config.TOGETHER_API_KEY)
    """
    import requests
    
    try:
        system_prompt = _build_system_prompt()
        
        response = requests.post(
            "https://api.together.xyz/inference",
            json={
                "model": "meta-llama/Llama-2-70b-chat-hf",  # Larger model for better JSON
                "prompt": f"{system_prompt}\n\nMessage: {text}\n\nResponse:",
                "max_tokens": 150,
                "temperature": 0.1,
                "stop": ["\n\n"]
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=15.0
        )
        
        response.raise_for_status()
        result = response.json()
        
        output = result["output"]["choices"][0]["text"].strip()
        return ModerationResponse.from_json(output)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Together AI error: {e}")
        raise RuntimeError(f"AI service error: {e}") 