"""
Discord bot for monitoring salvage yards for Dodge truck listings.
Periodically checks multiple salvage yard websites and sends notifications
to a Discord channel when new listings are found.
"""

import discord
from discord.ext import tasks
import asyncio
import logging
from typing import List

from config import Config
from database import Database
from utils import setup_logging, format_discord_message, generate_listing_id
from scrapers import PickNPullScraper, IPullUPullScraper, BucksAutoScraper


# Set up logging
logger = setup_logging(Config.LOG_LEVEL)


class DodgeTruckNotifier(discord.Client):
    """Discord bot for Dodge truck salvage yard notifications."""
    
    def __init__(self):
        """Initialize the bot."""
        # Set up Discord intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(intents=intents)
        
        self.database = Database(Config.DATABASE_PATH)
        self.scrapers = []
        self.channel_id = int(Config.DISCORD_CHANNEL_ID)
        self.test_mode = Config.TEST_MODE
    
    async def setup_hook(self):
        """Set up the bot after login."""
        # Initialize database
        await self.database.initialize()
        
        # Initialize scrapers
        self.scrapers = [
            PickNPullScraper(Config),
            IPullUPullScraper(Config),
            BucksAutoScraper(Config),
        ]
        
        for scraper in self.scrapers:
            await scraper.initialize()
        
        # Start the periodic check task
        self.check_listings.start()
        
        logger.info("Bot setup complete")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info(f"Check interval: {Config.CHECK_INTERVAL_MINUTES} minutes")
        logger.info(f"Test mode: {self.test_mode}")
        
        # Log channel info
        channel = self.get_channel(self.channel_id)
        if channel:
            logger.info(f"Notification channel: #{channel.name} in {channel.guild.name}")
        else:
            logger.error(f"Could not find channel with ID {self.channel_id}")
    
    async def on_message(self, message):
        """Handle incoming messages."""
        # Don't respond to ourselves
        if message.author == self.user:
            return
        
        # Simple command to manually trigger a check
        if message.content.startswith("!check"):
            logger.info(f"Manual check triggered by {message.author}")
            await message.channel.send("🔍 Checking salvage yards for new listings...")
            
            new_count = await self.check_all_scrapers()
            
            if new_count > 0:
                await message.channel.send(f"✅ Found {new_count} new listing(s)!")
            else:
                await message.channel.send("✅ No new listings found.")
        
        # Command to show bot status
        elif message.content.startswith("!status"):
            listing_count = await self.database.get_listing_count()
            status_msg = (
                f"📊 **Bot Status**\n"
                f"• Total listings tracked: {listing_count}\n"
                f"• Check interval: {Config.CHECK_INTERVAL_MINUTES} minutes\n"
                f"• Active scrapers: {len(self.scrapers)}\n"
                f"• Test mode: {self.test_mode}"
            )
            await message.channel.send(status_msg)
    
    @tasks.loop(minutes=Config.CHECK_INTERVAL_MINUTES)
    async def check_listings(self):
        """Periodically check all salvage yards for new listings."""
        logger.info("Starting scheduled check of salvage yards")
        
        try:
            new_count = await self.check_all_scrapers()
            logger.info(f"Scheduled check complete. Found {new_count} new listing(s)")
        except Exception as e:
            logger.error(f"Error during scheduled check: {e}", exc_info=True)
    
    @check_listings.before_loop
    async def before_check_listings(self):
        """Wait until the bot is ready before starting the loop."""
        await self.wait_until_ready()
        logger.info("Bot ready, starting periodic checks")
    
    async def check_all_scrapers(self) -> int:
        """
        Check all scrapers for new listings.
        
        Returns:
            Number of new listings found
        """
        new_listing_count = 0
        
        for scraper in self.scrapers:
            try:
                logger.info(f"Checking {scraper.get_name()}")
                listings = await scraper.scrape()
                
                for listing in listings:
                    # Check if listing is new
                    listing_id = generate_listing_id(listing)
                    
                    if not await self.database.is_listing_seen(listing_id):
                        # New listing found
                        logger.info(f"New listing found: {listing_id}")
                        
                        # Add to database
                        await self.database.add_listing(listing)
                        
                        # Send Discord notification
                        await self.send_notification(listing)
                        
                        new_listing_count += 1
                
            except Exception as e:
                logger.error(f"Error checking {scraper.get_name()}: {e}", exc_info=True)
        
        return new_listing_count
    
    async def send_notification(self, listing: dict):
        """
        Send a notification to Discord for a new listing.
        
        Args:
            listing: Dictionary containing listing information
        """
        if self.test_mode:
            logger.info(f"TEST MODE: Would send notification: {listing}")
            return
        
        try:
            channel = self.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Channel {self.channel_id} not found")
                return
            
            message = format_discord_message(listing)
            await channel.send(message)
            
            logger.info(f"Notification sent for listing: {generate_listing_id(listing)}")
        
        except discord.errors.Forbidden:
            logger.error("Bot does not have permission to send messages to the channel")
        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
    
    async def close(self):
        """Clean up when the bot is shutting down."""
        logger.info("Shutting down bot")
        
        # Close scrapers
        for scraper in self.scrapers:
            await scraper.close()
        
        await super().close()


def main():
    """Main entry point for the bot."""
    # Validate configuration
    is_valid, error_message = Config.validate()
    if not is_valid:
        logger.error(f"Configuration error: {error_message}")
        logger.error("Please check your .env file and environment variables")
        return
    
    # Create and run bot
    bot = DodgeTruckNotifier()
    
    try:
        bot.run(Config.DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)


if __name__ == "__main__":
    main()
