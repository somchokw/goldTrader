import logging
import sys
import re
from bot import run_bot
from keep_alive import keep_alive

class CloudflareHTMLFilter(logging.Filter):
    """Filter out massive Cloudflare HTML dumps from discord.py logs."""
    def filter(self, record):
        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            if "cf-error-details" in str(exc_value) or "Cloudflare Ray ID" in str(exc_value):
                record.msg = f"{record.msg} (Cloudflare 502/403 Blocked by Discord API. HTML hidden.)"
                record.exc_info = None # Strip the traceback to hide the HTML
        elif isinstance(record.msg, str) and ("cf-error-details" in record.msg or "Cloudflare Ray ID" in record.msg):
            record.msg = "Cloudflare HTML error suppressed."
        return True

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("gold_trader.log")
        ]
    )
    # Suppress verbose third party logs
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord").addFilter(CloudflareHTMLFilter())
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("yfinance").addFilter(CloudflareHTMLFilter())
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

if __name__ == "__main__":
    setup_logging()
    keep_alive()
    run_bot()
