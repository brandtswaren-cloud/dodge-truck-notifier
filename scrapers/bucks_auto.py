"""
Scraper for Buck's Auto salvage yards.
Website: bucksautoparts.com
"""

import logging
import re
from typing import List
from .base_scraper import BaseScraper
from utils import parse_year


logger = logging.getLogger("dodge_truck_notifier.scraper.bucks_auto")


class BucksAutoScraper(BaseScraper):
    """Scraper for Buck's Auto salvage yards."""
    
    def get_name(self) -> str:
        """Get the name of the salvage yard."""
        return "Buck's Auto"
    
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
        Scrape Buck's Auto website for Dodge truck listings.
        
        Returns:
            List of listing dictionaries
        """
        listings = []
        
        # Buck's Auto Calgary and Edmonton locations
        # Using correct domain: bucksautoparts.com
        locations = [
            ("Calgary", "https://www.bucksautoparts.com/our-locations/calgary?part="),
            ("Edmonton", "https://www.bucksautoparts.com/our-locations/edmonton?part="),
        ]
        
        for location_name, location_url in locations:
            try:
                logger.info(f"Scraping Buck's Auto {location_name}")
                
                html = await self.fetch_page(location_url)
                if not html:
                    logger.warning(f"Failed to fetch Buck's Auto {location_name}")
                    continue
                
                soup = self.parse_html(html)
                if not soup:
                    continue
                
                # Parse the vehicle table
                # Try to find table rows with vehicle data
                vehicle_tables = soup.find_all('table', class_=lambda x: x and ('inventory' in str(x).lower() or 'vehicle' in str(x).lower()))
                
                if not vehicle_tables:
                    # Try to find any tables
                    vehicle_tables = soup.find_all('table')
                
                for table in vehicle_tables:
                    # Find all rows in the table
                    rows = table.find_all('tr')
                    
                    # Skip header row(s)
                    for row in rows:
                        try:
                            # Get all cells in the row
                            cells = row.find_all(['td', 'th'])
                            
                            if len(cells) == 0:
                                continue
                            
                            # Convert row to text for checking
                            row_text = row.get_text(separator=' ', strip=True)
                            
                            # Skip header rows
                            if 'year' in row_text.lower() and 'make' in row_text.lower():
                                continue
                            
                            # Check if it contains "Dodge" and "Ram"
                            if not (("dodge" in row_text.lower() and "ram" in row_text.lower()) or
                                   self._is_ram_model(row_text)):
                                continue
                            
                            # Try to extract year (look for 4-digit number)
                            year = None
                            for cell in cells:
                                cell_text = cell.get_text(strip=True)
                                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', cell_text)
                                if year_match:
                                    potential_year = parse_year(year_match.group(1))
                                    if potential_year and self.config.YEAR_MIN <= potential_year <= self.config.YEAR_MAX:
                                        year = potential_year
                                        break
                            
                            if not year:
                                continue
                            
                            # Extract make
                            make = "Dodge"
                            
                            # Extract model
                            model = "Ram"
                            model_match = re.search(r'ram\s*(\d{4})?', row_text, re.IGNORECASE)
                            if model_match:
                                if model_match.group(1):
                                    model = f"Ram {model_match.group(1)}"
                                else:
                                    # Try to find model number separately
                                    ram_number = re.search(r'\b(1500|2500|3500)\b', row_text)
                                    if ram_number:
                                        model = f"Ram {ram_number.group(1)}"
                            
                            # Try to extract color if available
                            color = None
                            for cell in cells:
                                cell_text = cell.get_text(strip=True).lower()
                                colors = ['white', 'black', 'silver', 'gray', 'grey', 'red', 'blue', 'green', 'yellow', 'orange', 'brown', 'tan', 'beige']
                                for color_name in colors:
                                    if color_name in cell_text:
                                        color = cell.get_text(strip=True)
                                        break
                                if color:
                                    break
                            
                            # Try to extract date
                            arrival_date = None
                            for cell in cells:
                                cell_text = cell.get_text(strip=True)
                                # Look for date patterns (MM/DD/YYYY, YYYY-MM-DD, etc.)
                                date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}', cell_text)
                                if date_match:
                                    arrival_date = date_match.group(0)
                                    break
                            
                            listing = {
                                "yard_name": self.get_name(),
                                "location": location_name,
                                "year": year,
                                "make": make,
                                "model": model,
                                "stock_number": None,
                                "vin": None,
                                "arrival_date": arrival_date,
                                "url": location_url,
                            }
                            
                            # Add color as notes if available
                            if color:
                                listing["notes"] = f"Color: {color}"
                            
                            if self.is_valid_listing(listing):
                                listings.append(listing)
                                logger.debug(f"Found valid listing: {year} {make} {model}")
                        
                        except Exception as e:
                            logger.debug(f"Error parsing vehicle row: {e}")
                            continue
                
                logger.info(f"Found {len([l for l in listings if l['location'] == location_name])} valid listings at Buck's Auto {location_name}")
                
            except Exception as e:
                logger.error(f"Error scraping Buck's Auto {location_name}: {e}")
        
        logger.info(f"Total Buck's Auto listings found: {len(listings)}")
        return listings
