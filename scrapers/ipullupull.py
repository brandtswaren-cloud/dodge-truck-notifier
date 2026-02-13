"""
Scraper for IPull-UPull salvage yards.
Website: ipullupullcanada.ca
"""

import logging
import re
from typing import List
from .base_scraper import BaseScraper
from utils import parse_year


logger = logging.getLogger("dodge_truck_notifier.scraper.ipullupull")


class IPullUPullScraper(BaseScraper):
    """Scraper for IPull-UPull salvage yards."""
    
    def get_name(self) -> str:
        """Get the name of the salvage yard."""
        return "IPull-UPull"
    
    def _is_ram_model(self, model_text: str) -> bool:
        """
        Check if model text contains Ram (not Dakota, Durango, etc.).
        
        Args:
            model_text: The model text to check
        
        Returns:
            True if it's a Ram model, False otherwise
        """
        if not model_text:
            return False
        
        model_lower = model_text.lower()
        
        # Must contain "ram"
        if "ram" not in model_lower:
            return False
        
        # Exclude non-Ram models
        excluded = ["dakota", "durango", "caravan", "charger", "challenger"]
        for excluded_model in excluded:
            if excluded_model in model_lower:
                return False
        
        return True
    
    async def scrape(self) -> List[dict]:
        """
        Scrape IPull-UPull website for Dodge truck listings.
        
        Returns:
            List of listing dictionaries
        """
        listings = []
        
        # IPull-UPull has only Edmonton location
        # Using correct domain: ipullupullcanada.ca
        inventory_url = "https://ipullupullcanada.ca/inventory/dodge/"
        location_name = "Edmonton"
        
        try:
            logger.info(f"Scraping IPull-UPull {location_name}")
            
            html = await self.fetch_page(inventory_url)
            if not html:
                logger.warning(f"Failed to fetch IPull-UPull {location_name}")
                return listings
            
            soup = self.parse_html(html)
            if not soup:
                return listings
            
            # Parse vehicle cards/items from the page
            # Try multiple possible selectors for vehicle cards
            vehicle_cards = soup.select('div.vehicle-card, div.inventory-item, div.car-item, article.vehicle')
            
            if not vehicle_cards:
                # Try finding divs that might contain vehicle information
                vehicle_cards = soup.find_all('div', class_=lambda x: x and ('vehicle' in str(x).lower() or 'inventory' in str(x).lower() or 'car' in str(x).lower()))
            
            logger.debug(f"Found {len(vehicle_cards)} potential vehicle elements")
            
            for card in vehicle_cards:
                try:
                    # Extract vehicle information
                    card_text = card.get_text(separator=' ', strip=True)
                    
                    # Check if it's a Dodge Ram
                    if not (("dodge" in card_text.lower() and "ram" in card_text.lower()) or 
                            self._is_ram_model(card_text)):
                        continue
                    
                    # Extract year - look for 4-digit numbers that could be years
                    year = None
                    year_patterns = re.findall(r'\b(19\d{2}|20\d{2})\b', card_text)
                    for year_str in year_patterns:
                        potential_year = parse_year(year_str)
                        if potential_year and self.config.YEAR_MIN <= potential_year <= self.config.YEAR_MAX:
                            year = potential_year
                            break
                    
                    if not year:
                        continue
                    
                    # Extract make - should be Dodge
                    make = "Dodge"
                    
                    # Extract model - try to find Ram with numbers
                    model = "Ram"
                    # First try to find specific Ram model numbers (1500, 2500, 3500)
                    ram_number = re.search(r'\b(1500|2500|3500)\b', card_text)
                    if ram_number:
                        model = f"Ram {ram_number.group(1)}"
                    else:
                        # Look for "Ram" followed by 4 digits (but not a year)
                        model_match = re.search(r'ram\s+(\d{4})', card_text, re.IGNORECASE)
                        if model_match and model_match.group(1) not in year_patterns:
                            model = f"Ram {model_match.group(1)}"
                    
                    # Extract VIN
                    vin = None
                    vin_elem = card.find(class_=lambda x: x and 'vin' in str(x).lower())
                    if vin_elem:
                        vin = vin_elem.text.strip()
                    else:
                        # Look for VIN pattern in text (17 alphanumeric characters)
                        vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', card_text)
                        if vin_match:
                            vin = vin_match.group(0)
                    
                    # Extract arrival/entry date
                    arrival_date = None
                    date_elem = card.find(class_=lambda x: x and ('date' in str(x).lower() or 'arrival' in str(x).lower()))
                    if date_elem:
                        arrival_date = date_elem.text.strip()
                    
                    # Generate listing URL
                    url_elem = card.find('a', href=True)
                    if url_elem and url_elem.get('href'):
                        href = url_elem['href']
                        if href.startswith('http'):
                            listing_url = href
                        else:
                            listing_url = f"https://ipullupullcanada.ca{href}" if href.startswith('/') else f"https://ipullupullcanada.ca/{href}"
                    else:
                        listing_url = inventory_url
                    
                    listing = {
                        "yard_name": self.get_name(),
                        "location": location_name,
                        "year": year,
                        "make": make,
                        "model": model,
                        "stock_number": None,
                        "vin": vin,
                        "arrival_date": arrival_date,
                        "url": listing_url,
                    }
                    
                    if self.is_valid_listing(listing):
                        listings.append(listing)
                        logger.debug(f"Found valid listing: {year} {make} {model}")
                
                except Exception as e:
                    logger.debug(f"Error parsing vehicle card: {e}")
                    continue
            
            logger.info(f"Found {len(listings)} valid listings at IPull-UPull {location_name}")
            
        except Exception as e:
            logger.error(f"Error scraping IPull-UPull {location_name}: {e}")
        
        return listings
