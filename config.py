import os
from dotenv import load_dotenv

load_dotenv()

# Feature Flags
HIGH_RISK_MODE_ENABLED = os.environ.get("HIGH_RISK_MODE_ENABLED", "False").lower() == "true"

# API Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

# Model Configuration
# Upgraded to next-gen Gemini 3.6 Flash by default
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini/gemini-3.6-flash")

# Trading Configurations
# Using TradingView for accurate Spot Gold pricing
SYMBOL = "XAUUSD"
EXCHANGE = "OANDA"
SCREENER = "cfd"
INSTRUMENT_TYPE = "CFD"

CONTRACT_SIZE = 100.0  # 1 standard lot = 100 ounces for Gold
MIN_LOT = 0.01
LOT_STEP = 0.01

DEFAULT_RISK_PERCENT = 1.0  # Safe mode 1%
HIGH_RISK_PERCENT = 50.0    # Sniper mode 50%
MAX_RISK_LIMIT = 50.0

MIN_RR_RATIO = 1.5  # High win-rate target (Reward must be >= 1.5x Risk)

# Rate Limiting & High-Win-Rate Sniper Controls (Patch 1.7.3)
MAX_DAILY_SIGNALS = int(os.environ.get("MAX_DAILY_SIGNALS", 10))
SIGNAL_COOLDOWN_MINUTES = int(os.environ.get("SIGNAL_COOLDOWN_MINUTES", 45))
MIN_PRICE_CHANGE_FOR_NEW_SIGNAL = float(os.environ.get("MIN_PRICE_CHANGE_FOR_NEW_SIGNAL", 5.0))

STALE_DATA_THRESHOLD_MINUTES = 45
