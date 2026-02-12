"""
Base scraper class for salvage yard websites.
Provides common functionality for all scrapers.
"""

import logging
import asyncio
import aiohttp
from typing import List, Optional
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup


logger = logging.getLogger("dodge_truck_notifier.scraper")


class BaseScraper(ABC):
    """Abstract base class for salvage yard scrapers."""
    
    def __init__(self, config):
        """
        Initialize the scraper.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize the HTTP session."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={'User-Agent': self.config.USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
            )
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with retry logic.
        
        Args:
            url: The URL to fetch
        
        Returns:
            Page content as string or None if failed
        """
        if not self.session:
            await self.initialize()
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                logger.debug(f"Fetching {url} (attempt {attempt + 1}/{self.config.MAX_RETRIES})")
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Rate limiting: delay between requests
                        await asyncio.sleep(self.config.REQUEST_DELAY)
                        return content
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
            
            # Exponential backoff for retries
            if attempt < self.config.MAX_RETRIES - 1:
                delay = self.config.RETRY_DELAY * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        logger.error(f"Failed to fetch {url} after {self.config.MAX_RETRIES} attempts")
        return None
    
    def parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """
        Parse HTML content with BeautifulSoup.
        
        Args:
            html: HTML content string
        
        Returns:
            BeautifulSoup object or None if parsing failed
        """
        try:
            return BeautifulSoup(html, 'lxml')
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return None
    
    def is_valid_listing(self, listing: dict) -> bool:
        """
        Check if a listing meets the filter criteria.
        
        Args:
            listing: Dictionary containing listing information
        
        Returns:
            True if listing is valid, False otherwise
        """
        from utils import is_year_in_range, is_target_location
        
        # Check year range
        year = listing.get("year")
        if not is_year_in_range(year, self.config.YEAR_MIN, self.config.YEAR_MAX):
            logger.debug(f"Listing filtered out: year {year} not in range")
            return False
        
        # Check location
        location = listing.get("location", "")
        if not is_target_location(location, self.config.TARGET_LOCATIONS):
            logger.debug(f"Listing filtered out: location {location} not in targets")
            return False
        
        # Check make (should contain "Dodge")
        make = listing.get("make", "").lower()
        if "dodge" not in make:
            logger.debug(f"Listing filtered out: make {make} is not Dodge")
            return False
        
        return True
    
    @abstractmethod
    async def scrape(self) -> List[dict]:
        """
        Scrape the salvage yard website for listings.
        
        Returns:
            List of listing dictionaries
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of the salvage yard.
        
        Returns:
            Name of the salvage yard
        """
        pass
