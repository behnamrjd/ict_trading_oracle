"""
Configuration settings for ICT Trading Bot
"""

import os
from pathlib import Path

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "YOUR_NEWS_API_KEY")

# Payment Configuration
ZARINPAL_MERCHANT_ID = os.getenv("ZARINPAL_MERCHANT_ID", "YOUR_ZARINPAL_MERCHANT")
CRYPTAPI_CALLBACK_URL = os.getenv("CRYPTAPI_CALLBACK_URL", "https://yourdomain.com/api")

# Database Configuration
BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = BASE_DIR / "data" / "ict_trading.db"

# Trading Configuration
TRADING_SYMBOL = "GC=F"  # Gold Futures
DEFAULT_TIMEFRAMES = {
    'swing': '1h',
    'scalping': '1m',
    'analysis': '1d'
}

# Subscription Plans
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'daily_signals': 3,
        'features': ['basic_ict_analysis', 'education', 'price_display']
    },
    'premium': {
        'name': 'Premium',
        'price': 49,
        'daily_signals': 50,
        'features': ['all_features']
    },
    'vip': {
        'name': 'VIP',
        'price': 149,
        'daily_signals': -1,  # Unlimited
        'features': ['everything', 'copy_trading', 'personal_consultation']
    }
}

# Admin Configuration - ADD YOUR USER ID HERE
ADMIN_IDS = [
    YOUR_USER_ID_HERE,  # Replace with your actual User ID from /start command
    123456789,          # Example admin ID
    987654321           # Example admin ID
]

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "logs" / "ict_trading.log"
