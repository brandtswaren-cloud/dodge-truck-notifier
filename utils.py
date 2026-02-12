"""
Utility functions for the Dodge Truck Notifier bot.
"""

import logging
from datetime import datetime
from typing import Optional


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger("dodge_truck_notifier")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler if not already present
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger


def is_year_in_range(year: Optional[int], min_year: int, max_year: int) -> bool:
    """
    Check if a year falls within the specified range.
    
    Args:
        year: The year to check
        min_year: Minimum year (inclusive)
        max_year: Maximum year (inclusive)
    
    Returns:
        True if year is in range, False otherwise
    """
    if year is None:
        return False
    return min_year <= year <= max_year


def is_target_location(location: str, target_locations: list[str]) -> bool:
    """
    Check if a location is in the target locations list.
    
    Args:
        location: The location to check
        target_locations: List of target locations
    
    Returns:
        True if location matches, False otherwise
    """
    if not location:
        return False
    
    location_lower = location.lower()
    return any(target.lower() in location_lower for target in target_locations)


def format_discord_message(listing: dict) -> str:
    """
    Format a listing as a Discord message.
    
    Args:
        listing: Dictionary containing listing information
    
    Returns:
        Formatted message string
    """
    message = "🚨 **New Dodge Truck Listing!**\n\n"
    
    if listing.get("year"):
        message += f"📅 **Year:** {listing['year']}\n"
    
    if listing.get("make") or listing.get("model"):
        make = listing.get("make", "")
        model = listing.get("model", "")
        message += f"🚗 **Make/Model:** {make} {model}\n"
    
    if listing.get("yard_name"):
        yard_info = listing["yard_name"]
        if listing.get("location"):
            yard_info += f" - {listing['location']}"
        message += f"🏢 **Yard:** {yard_info}\n"
    
    if listing.get("url"):
        message += f"🔗 **Link:** {listing['url']}\n"
    
    if listing.get("stock_number"):
        message += f"📦 **Stock #:** {listing['stock_number']}\n"
    
    if listing.get("arrival_date"):
        message += f"📍 **Arrived:** {listing['arrival_date']}\n"
    
    if listing.get("notes"):
        message += f"\n💬 {listing['notes']}\n"
    
    return message


def parse_year(year_str: str) -> Optional[int]:
    """
    Parse a year string to integer.
    
    Args:
        year_str: String representation of year
    
    Returns:
        Year as integer or None if parsing fails
    """
    if not year_str:
        return None
    
    try:
        # Remove any non-digit characters
        year_digits = ''.join(c for c in str(year_str) if c.isdigit())
        if len(year_digits) >= 4:
            return int(year_digits[:4])
        return None
    except (ValueError, TypeError):
        return None


def generate_listing_id(listing: dict) -> str:
    """
    Generate a unique identifier for a listing.
    
    Args:
        listing: Dictionary containing listing information
    
    Returns:
        Unique identifier string
    """
    # Use URL if available as it's the most reliable unique identifier
    if listing.get("url"):
        return listing["url"]
    
    # Otherwise, create a composite key
    parts = [
        listing.get("yard_name", ""),
        listing.get("location", ""),
        str(listing.get("year", "")),
        listing.get("make", ""),
        listing.get("model", ""),
        listing.get("stock_number", ""),
    ]
    
    return "|".join(parts)
