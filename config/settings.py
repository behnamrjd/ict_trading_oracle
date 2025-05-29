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
        'price': 49000,  # Toman
        'daily_signals': 50,
        'features': ['all_features', 'premium_analysis', 'email_support']
    },
    'vip': {
        'name': 'VIP',
        'price': 149000,  # Toman
        'daily_signals': -1,  # Unlimited
        'features': ['everything', 'copy_trading', 'personal_consultation', 'priority_support']
    }
}

# Admin Configuration - REPLACE WITH YOUR ACTUAL USER IDS
ADMIN_IDS = [
    262182607,  # Replace this number with your actual User ID from /start command
    987654321   # Example admin ID
]

# AI Configuration
AI_MODEL_PATH = BASE_DIR / "ai_models" / "trained_models"
AI_CONFIDENCE_THRESHOLD = int(os.getenv("AI_CONFIDENCE_THRESHOLD", "70"))
AI_RETRAIN_INTERVAL = int(os.getenv("AI_RETRAIN_INTERVAL", "7"))

# Monitoring Configuration
MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
MONITORING_INTERVAL = int(os.getenv("MONITORING_INTERVAL", "60"))
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "admin@yourdomain.com")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "logs" / "ict_trading.log"

# Performance Configuration
MAX_CONCURRENT_USERS = 1000
DATABASE_POOL_SIZE = 10
API_TIMEOUT = 30
CACHE_DURATION = 300  # 5 minutes

# Security Configuration
RATE_LIMIT_PER_MINUTE = 60
MAX_SIGNAL_REQUESTS_PER_HOUR = 100
SESSION_TIMEOUT = 3600  # 1 hour

# Backtest Configuration
BACKTEST_DAYS = 7
SIGNALS_PER_DAY = 10
BACKTEST_ENABLED = True
