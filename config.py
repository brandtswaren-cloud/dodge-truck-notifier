"""
Configuration management for the Dodge Truck Notifier bot.
Loads environment variables and provides configuration settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for bot settings."""
    
    # Discord Configuration
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_CHANNEL_ID: str = os.getenv("DISCORD_CHANNEL_ID", "")
    
    # Bot Configuration
    CHECK_INTERVAL_MINUTES: int = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "listings.db")
    
    # Scraping Configuration
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY: float = 3.0  # Delay between requests in seconds
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # Initial retry delay in seconds
    
    # Search Criteria
    TARGET_MAKE: str = "Dodge"
    TARGET_MODELS: list = ["RAM", "Dakota", "Truck"]
    YEAR_MIN: int = 1994
    YEAR_MAX: int = 2026
    TARGET_LOCATIONS: list = ["Calgary", "Edmonton"]
    
    # User-Agent for web scraping
    USER_AGENT: str = "DodgeTruckNotifierBot/1.0 (Salvage Yard Monitor; +https://github.com/brandtswaren-cloud/dodge-truck-notifier)"
    
    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        Validate that required configuration is present.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not cls.DISCORD_BOT_TOKEN:
            return False, "DISCORD_BOT_TOKEN is required"
        
        if not cls.DISCORD_CHANNEL_ID:
            return False, "DISCORD_CHANNEL_ID is required"
        
        if cls.CHECK_INTERVAL_MINUTES < 1:
            return False, "CHECK_INTERVAL_MINUTES must be at least 1"
        
        return True, None
