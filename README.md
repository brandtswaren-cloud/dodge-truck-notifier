# Dodge Truck Notifier Discord Bot

A Discord bot that monitors salvage yard websites for 1994-2026 Dodge Trucks and sends notifications to a Discord channel when new listings are found.

## Features

- 🔍 **Automated Monitoring**: Periodically checks multiple salvage yard websites
- 🎯 **Smart Filtering**: Only tracks Dodge trucks from 1994-2026 in Calgary and Edmonton
- 📊 **Persistent Storage**: Uses SQLite database to prevent duplicate notifications
- 🚀 **Easy Deployment**: Deploy for free on Railway.app, Render.com, or Fly.io
- 🛡️ **Robust Error Handling**: Graceful handling of website downtime and errors
- 📝 **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Monitored Salvage Yards

1. **Pick-n-Pull** - Calgary and Edmonton locations
2. **IPull-UPull** - Calgary and Edmonton locations
3. **Buck's Auto** - Calgary and Edmonton locations

## Prerequisites

- Python 3.9 or higher
- A Discord account
- A GitHub account (for deployment)

## Setup Instructions

### 1. Create a Discord Bot

1. Go to https://discord.com/developers/applications
2. Click "New Application" and give it a name (e.g., "Dodge Truck Notifier")
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot" to create a bot user
5. Under "Privileged Gateway Intents", enable:
   - ✅ Message Content Intent
6. Click "Reset Token" and copy the bot token (you'll need this later)
7. Go to the "OAuth2" → "URL Generator" section
8. Select scopes:
   - ✅ bot
9. Select bot permissions:
   - ✅ Send Messages
   - ✅ Read Messages/View Channels
10. Copy the generated URL and open it in your browser to invite the bot to your server

### 2. Get Your Discord Channel ID

1. Open Discord and go to User Settings
2. Go to "Advanced" and enable "Developer Mode"
3. Right-click on the `#listings` channel (or your preferred channel)
4. Click "Copy ID" to get the channel ID

### 3. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/brandtswaren-cloud/dodge-truck-notifier.git
cd dodge-truck-notifier

# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred text editor
```

Edit `.env` and add your credentials:
```env
DISCORD_BOT_TOKEN=your_actual_bot_token_here
DISCORD_CHANNEL_ID=your_actual_channel_id_here
CHECK_INTERVAL_MINUTES=30
LOG_LEVEL=INFO
```

### 4. Install Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running Locally

### Test the Bot

```bash
# Run the bot
python bot.py
```

The bot will:
- Connect to Discord
- Initialize the database
- Start checking salvage yards every 30 minutes (or your configured interval)

### Manual Commands

Once the bot is running, you can use these commands in Discord:

- `!check` - Manually trigger a check for new listings
- `!status` - Show bot status and statistics

### Test Mode

To test without sending Discord messages, set `TEST_MODE=true` in your `.env` file.

## Deployment

### Deploy on Railway.app (Recommended)

Railway.app offers 500 hours/month of free usage, which is perfect for this bot.

1. **Create a Railway Account**
   - Go to https://railway.app
   - Sign up with your GitHub account

2. **Create a New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub account
   - Select the `dodge-truck-notifier` repository

3. **Add Environment Variables**
   - Click on your deployment
   - Go to "Variables" tab
   - Add the following variables:
     - `DISCORD_BOT_TOKEN`: Your Discord bot token
     - `DISCORD_CHANNEL_ID`: Your Discord channel ID
     - `CHECK_INTERVAL_MINUTES`: 30 (or your preferred interval)
     - `LOG_LEVEL`: INFO

4. **Deploy**
   - Railway will automatically detect the `Dockerfile` and build your bot
   - Click "Deploy" to start the bot
   - Monitor logs in the "Deployments" tab

5. **Monitor**
   - View logs in real-time from the Railway dashboard
   - The bot will restart automatically if it crashes

### Deploy on Render.com (Alternative)

Render.com offers a free tier with auto-deploys from GitHub.

1. **Create a Render Account**
   - Go to https://render.com
   - Sign up with your GitHub account

2. **Create a New Web Service**
   - Click "New +" → "Background Worker"
   - Connect your GitHub repository
   - Configure:
     - **Name**: dodge-truck-notifier
     - **Environment**: Docker
     - **Plan**: Free

3. **Add Environment Variables**
   - Add the same variables as Railway:
     - `DISCORD_BOT_TOKEN`
     - `DISCORD_CHANNEL_ID`
     - `CHECK_INTERVAL_MINUTES`
     - `LOG_LEVEL`

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy on every push to main

### Deploy on Fly.io (Alternative)

Fly.io offers a generous free tier.

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to Fly.io**
   ```bash
   fly auth login
   ```

3. **Launch the App**
   ```bash
   fly launch
   ```

4. **Set Environment Variables**
   ```bash
   fly secrets set DISCORD_BOT_TOKEN=your_token_here
   fly secrets set DISCORD_CHANNEL_ID=your_channel_id_here
   fly secrets set CHECK_INTERVAL_MINUTES=30
   fly secrets set LOG_LEVEL=INFO
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

## Project Structure

```
dodge-truck-notifier/
├── bot.py                      # Main Discord bot
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py        # Base scraper class
│   ├── picknpull.py           # Pick-n-Pull scraper
│   ├── ipullupull.py          # IPull-UPull scraper
│   └── bucks_auto.py          # Buck's Auto scraper
├── database.py                 # SQLite database management
├── config.py                   # Configuration management
├── utils.py                    # Utility functions
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── railway.json                # Railway deployment config
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
└── README.md                  # This file
```

## Troubleshooting

### Bot won't connect to Discord

**Error**: `discord.errors.LoginFailure`

**Solution**: 
- Double-check your `DISCORD_BOT_TOKEN` in the `.env` file
- Make sure there are no extra spaces or quotes around the token
- Generate a new token from the Discord Developer Portal if needed

### Bot can't find the channel

**Error**: Channel not found or permission denied

**Solution**:
- Verify the `DISCORD_CHANNEL_ID` is correct
- Make sure the bot has been invited to your server
- Check that the bot has "View Channel" and "Send Messages" permissions

### Website scraping not working

**Error**: No listings found or scraper errors

**Solution**:
- Salvage yard websites may have changed their structure
- Check the logs for specific error messages
- The scraper files may need to be updated (see "Maintenance" section below)

### Database errors

**Error**: Database locked or permission errors

**Solution**:
- Make sure the bot has write permissions in its directory
- If on a deployment platform, ensure persistent storage is configured
- Delete `listings.db` to start fresh (you'll lose history)

## Maintenance

### Updating the Bot

If the salvage yard websites change and scrapers stop working:

1. Check the logs to identify which scraper is failing
2. Visit the salvage yard website to see what changed
3. Update the corresponding scraper file in `scrapers/`
4. Test locally before deploying
5. Push changes to GitHub (auto-deploys on Railway/Render)

### Adding New Salvage Yards

To add a new salvage yard:

1. Create a new scraper file in `scrapers/` (e.g., `new_yard.py`)
2. Extend the `BaseScraper` class
3. Implement the `scrape()` and `get_name()` methods
4. Add the new scraper to `scrapers/__init__.py`
5. Import and add it to the scrapers list in `bot.py`

### Database Management

The SQLite database (`listings.db`) stores all seen listings.

**Backup**:
```bash
cp listings.db listings_backup.db
```

**Reset** (clear all history):
```bash
rm listings.db
# Restart the bot to create a new database
```

**Query** (view listings):
```bash
sqlite3 listings.db "SELECT * FROM listings ORDER BY first_seen DESC LIMIT 10;"
```

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | - | Your Discord bot token |
| `DISCORD_CHANNEL_ID` | Yes | - | Discord channel ID for notifications |
| `CHECK_INTERVAL_MINUTES` | No | 30 | How often to check for new listings |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `TEST_MODE` | No | false | If true, doesn't send Discord messages |
| `DATABASE_PATH` | No | listings.db | Path to SQLite database file |

## Important Notes

- **Respect robots.txt**: The bot includes delays between requests to be respectful
- **Rate Limiting**: 3-5 second delays between requests to avoid overloading websites
- **User-Agent**: Bot identifies itself properly in HTTP headers
- **Target Locations**: Only Calgary and Edmonton are monitored
- **Year Range**: Only 1994-2026 vehicles are tracked
- **Persistent Storage**: Database survives bot restarts

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Open an issue on GitHub with:
   - Description of the problem
   - Error messages from logs
   - Steps to reproduce

## Disclaimer

This bot is for personal use to monitor salvage yard listings. Please:
- Respect the websites' terms of service
- Use reasonable check intervals (30+ minutes recommended)
- Don't overload the websites with requests
- Verify any information directly with the salvage yards

---

**Happy hunting for Dodge truck parts! 🚚🔧**
