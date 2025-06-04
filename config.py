"""Configuration management for co-parent filter bot."""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Moderation profiles for different types of problematic behaviors
MODERATION_PROFILES = {
    "manipulative_coparent": {
        "name": "Manipulative Co-Parent",
        "description": "Someone who tends toward performative behavior, narrative crafting, and inconsistent actions",
        "behaviors": [
            "performative posturing without follow-through",
            "crafting narratives about being good while failing to take positive action",
            "manipulative language designed to appear reasonable",
            "deflection from actual logistics to emotional manipulation",
            "making themselves appear as the victim or hero",
            "saying the right things but consistently failing to act",
            "using guilt, blame, or emotional pressure instead of facts",
            "grandstanding or virtue signaling without substance"
        ],
        "permissive_mode": True,  # Only block OBVIOUSLY problematic content
    },
    "standard": {
        "name": "Standard Moderation",
        "description": "Basic co-parenting topic filtering",
        "behaviors": [],
        "permissive_mode": True,
    },
}


class Config:
    """Centralized configuration for the bot."""
    
    # Telegram Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Monitoring Configuration
    TARGET_USERNAME: str = os.getenv("TARGET_USERNAME", "parkerrralex")
    
    # Moderation Configuration
    MODERATION_PROFILE: str = os.getenv("MODERATION_PROFILE", "manipulative_coparent")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration is present."""
        missing = []
        
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        
        if cls.MODERATION_PROFILE not in MODERATION_PROFILES:
            missing.append(f"MODERATION_PROFILE (valid options: {', '.join(MODERATION_PROFILES.keys())})")
        
        if missing:
            raise ValueError(
                f"Missing or invalid configuration: {', '.join(missing)}\n"
                f"Please check your .env file or environment variables."
            )
    
    @classmethod
    def get_target_username_normalized(cls) -> str:
        """Get target username without @ prefix."""
        username = cls.TARGET_USERNAME.strip()
        return username.lstrip("@")
    
    @classmethod
    def get_moderation_profile(cls) -> dict:
        """Get the current moderation profile configuration."""
        return MODERATION_PROFILES.get(cls.MODERATION_PROFILE, MODERATION_PROFILES["standard"])


# Initialize and validate configuration on import
config = Config() 