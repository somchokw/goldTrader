import os
from dotenv import load_dotenv

load_dotenv()

# Feature Flags
HIGH_RISK_MODE_ENABLED = os.environ.get("HIGH_RISK_MODE_ENABLED", "False").lower() == "true"

# API Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

# Model Configuration
# Use stable version instead of 'latest' for reproducibility
LLM_MODEL = "gemini/gemini-3.5-flash"

# Trading Configurations
# Note: XAUUSD=X does not exist on Yahoo Finance. We must use GC=F (Futures).
SYMBOL = "GC=F"
INSTRUMENT_TYPE = "FUTURES" if "F" in SYMBOL else "CFD"

CONTRACT_SIZE = 100.0  # 1 standard lot = 100 ounces for Gold
MIN_LOT = 0.01
LOT_STEP = 0.01

DEFAULT_RISK_PERCENT = 1.0  # Safe mode 1%
HIGH_RISK_PERCENT = 50.0    # Sniper mode 50%
MAX_RISK_LIMIT = 50.0

MIN_RR_RATIO = 1.5

STALE_DATA_THRESHOLD_MINUTES = 45
