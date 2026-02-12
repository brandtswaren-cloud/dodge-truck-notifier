"""
Database management for the Dodge Truck Notifier bot.
Handles SQLite database operations for storing and tracking listings.
"""

import aiosqlite
import logging
from typing import Optional, List
from datetime import datetime


logger = logging.getLogger("dodge_truck_notifier.database")


class Database:
    """Database manager for tracking seen listings."""
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
    
    async def initialize(self):
        """Create database tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT UNIQUE NOT NULL,
                    yard_name TEXT,
                    location TEXT,
                    year INTEGER,
                    make TEXT,
                    model TEXT,
                    stock_number TEXT,
                    url TEXT,
                    arrival_date TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_listing_id 
                ON listings(listing_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_first_seen 
                ON listings(first_seen)
            """)
            
            await db.commit()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    async def is_listing_seen(self, listing_id: str) -> bool:
        """
        Check if a listing has been seen before.
        
        Args:
            listing_id: Unique identifier for the listing
        
        Returns:
            True if listing exists in database, False otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM listings WHERE listing_id = ?",
                (listing_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] > 0
    
    async def add_listing(self, listing: dict) -> bool:
        """
        Add a new listing to the database.
        
        Args:
            listing: Dictionary containing listing information
        
        Returns:
            True if listing was added, False if it already existed
        """
        from utils import generate_listing_id
        
        listing_id = generate_listing_id(listing)
        
        # Check if already exists
        if await self.is_listing_seen(listing_id):
            return False
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO listings 
                    (listing_id, yard_name, location, year, make, model, 
                     stock_number, url, arrival_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    listing_id,
                    listing.get("yard_name"),
                    listing.get("location"),
                    listing.get("year"),
                    listing.get("make"),
                    listing.get("model"),
                    listing.get("stock_number"),
                    listing.get("url"),
                    listing.get("arrival_date")
                ))
                await db.commit()
            
            logger.info(f"Added new listing to database: {listing_id}")
            return True
        
        except aiosqlite.IntegrityError:
            logger.warning(f"Listing already exists: {listing_id}")
            return False
        except Exception as e:
            logger.error(f"Error adding listing to database: {e}")
            return False
    
    async def update_last_checked(self, listing_id: str):
        """
        Update the last_checked timestamp for a listing.
        
        Args:
            listing_id: Unique identifier for the listing
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE listings 
                    SET last_checked = CURRENT_TIMESTAMP 
                    WHERE listing_id = ?
                """, (listing_id,))
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating last_checked: {e}")
    
    async def get_all_listings(self) -> List[dict]:
        """
        Get all listings from the database.
        
        Returns:
            List of listing dictionaries
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM listings 
                ORDER BY first_seen DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_listing_count(self) -> int:
        """
        Get total count of listings in database.
        
        Returns:
            Number of listings
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM listings") as cursor:
                result = await cursor.fetchone()
                return result[0]
    
    async def cleanup_old_listings(self, days: int = 90):
        """
        Remove listings older than specified days.
        
        Args:
            days: Number of days to keep listings
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM listings 
                    WHERE first_seen < datetime('now', '-' || ? || ' days')
                """, (days,))
                await db.commit()
            
            logger.info(f"Cleaned up listings older than {days} days")
        except Exception as e:
            logger.error(f"Error cleaning up old listings: {e}")
