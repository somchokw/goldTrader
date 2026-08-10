import logging
import sys
from bot import run_bot
from keep_alive import keep_alive

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
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

if __name__ == "__main__":
    setup_logging()
    keep_alive()
    run_bot()
