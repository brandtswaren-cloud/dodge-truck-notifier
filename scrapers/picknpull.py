"""
Scraper for Pick-n-Pull salvage yards.
Website: picknpull.com
"""

import logging
from typing import List
from .base_scraper import BaseScraper
from utils import parse_year


logger = logging.getLogger("dodge_truck_notifier.scraper.picknpull")


class PickNPullScraper(BaseScraper):
    """Scraper for Pick-n-Pull salvage yards."""
    
    def get_name(self) -> str:
        """Get the name of the salvage yard."""
        return "Pick-n-Pull"
    
    async def scrape(self) -> List[dict]:
        """
        Scrape Pick-n-Pull website for Dodge truck listings.
        
        Returns:
            List of listing dictionaries
        """
        listings = []
        
        # Pick-n-Pull search URLs for Ram 1500, 2500, 3500 in Calgary and Edmonton
        # Format: (location_name, zip_code, model_name, model_id)
        search_configs = [
            ("Calgary", "T2P0A8", "Ram 1500", "1634"),
            ("Calgary", "T2P0A8", "Ram 2500", "1636"),
            ("Calgary", "T2P0A8", "Ram 3500", "1638"),
            ("Edmonton", "T5T6M8", "Ram 1500", "1634"),
            ("Edmonton", "T5T6M8", "Ram 2500", "1636"),
            ("Edmonton", "T5T6M8", "Ram 3500", "1638"),
        ]
        
        for location_name, zip_code, model_name, model_id in search_configs:
            try:
                # Build the search URL with proper parameters
                search_url = (
                    f"https://www.picknpull.com/check-inventory/vehicle-search?"
                    f"make=117&model={model_id}&distance=25&zip={zip_code}&year=1994-2025"
                )
                
                logger.info(f"Scraping Pick-n-Pull {location_name} for {model_name}")
                
                html = await self.fetch_page(search_url)
                if not html:
                    logger.warning(f"Failed to fetch Pick-n-Pull {location_name} {model_name}")
                    continue
                
                soup = self.parse_html(html)
                if not soup:
                    continue
                
                # Parse the search results
                # Look for vehicle rows in the results table
                vehicle_rows = soup.select('div.row.vehicle-row, tr.vehicle-row, div.vehicle-item')
                
                if not vehicle_rows:
                    # Try alternative selectors
                    vehicle_rows = soup.find_all('div', class_=lambda x: x and 'vehicle' in x.lower())
                
                for row in vehicle_rows:
                    try:
                        # Extract vehicle information from the row
                        # This may need adjustment based on actual HTML structure
                        
                        # Try to find year
                        year_elem = row.find(class_=lambda x: x and 'year' in str(x).lower())
                        if not year_elem:
                            year_elem = row.find('span', text=lambda t: t and t.strip().isdigit() and len(t.strip()) == 4)
                        
                        year = None
                        if year_elem:
                            potential_year = parse_year(year_elem.text.strip())
                            # Validate year is in reasonable range
                            if potential_year and 1900 <= potential_year <= 2100:
                                year = potential_year
                        
                        # Try to find make
                        make_elem = row.find(class_=lambda x: x and 'make' in str(x).lower())
                        make = make_elem.text.strip() if make_elem else "Dodge"
                        
                        # Try to find model - use the model_name from our config since we're searching specifically
                        model = model_name
                        
                        # Try to find stock number
                        stock_elem = row.find(class_=lambda x: x and ('stock' in str(x).lower() or 'id' in str(x).lower()))
                        if not stock_elem:
                            stock_elem = row.find('a', href=True)
                        stock_number = stock_elem.text.strip() if stock_elem else None
                        
                        # Try to find arrival date
                        date_elem = row.find(class_=lambda x: x and 'date' in str(x).lower())
                        arrival_date = date_elem.text.strip() if date_elem else None
                        
                        # Generate listing URL
                        url_elem = row.find('a', href=True)
                        if url_elem and url_elem.get('href'):
                            href = url_elem['href']
                            if href.startswith('http'):
                                listing_url = href
                            else:
                                listing_url = f"https://www.picknpull.com{href}" if href.startswith('/') else f"https://www.picknpull.com/{href}"
                        else:
                            listing_url = search_url
                        
                        listing = {
                            "yard_name": self.get_name(),
                            "location": location_name,
                            "year": year,
                            "make": make if make else "Dodge",
                            "model": model,
                            "stock_number": stock_number,
                            "vin": None,
                            "arrival_date": arrival_date,
                            "url": listing_url,
                        }
                        
                        if self.is_valid_listing(listing):
                            listings.append(listing)
                            logger.debug(f"Found valid listing: {year} {make} {model}")
                    
                    except Exception as e:
                        logger.debug(f"Error parsing vehicle row: {e}")
                        continue
                
                logger.info(f"Found {len([l for l in listings if l['location'] == location_name and l['model'] == model_name])} listings for Pick-n-Pull {location_name} {model_name}")
                
            except Exception as e:
                logger.error(f"Error scraping Pick-n-Pull {location_name} {model_name}: {e}")
        
        logger.info(f"Total Pick-n-Pull listings found: {len(listings)}")
        return listings
