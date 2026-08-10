import requests
import logging
from config import DISCORD_WEBHOOK_URL

logger = logging.getLogger(__name__)

def send_discord_notify(message):
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "your_discord_webhook_url_here_optional":
        logger.warning("Discord Webhook URL not configured. Skipping notification.")
        return False
    
    # Discord messages are limited to 2000 characters
    if len(message) > 1950:
        message = message[:1950] + "\n...[Truncated]"
        
    data = {
        "content": f"🤖 **Gold Trading AI Update** 📈\n```text\n{message}\n```",
        "allowed_mentions": {"parse": []} # Prevent accidental @mentions
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        response.raise_for_status()
        logger.info("Successfully sent Discord notification.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False
