# Database configuration 
"""
Database configuration and setup
"""

import sqlite3
from pathlib import Path
from config.settings import DATABASE_PATH
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """مدیریت پایگاه داده"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """ایجاد جداول پایگاه داده"""
        try:
            # ایجاد فولدر data اگر وجود ندارد
            self.db_path.parent.mkdir(exist_ok=True)
            
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # جدول کاربران
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    agreed_terms INTEGER DEFAULT 0,
                    join_date TEXT,
                    last_activity TEXT,
                    is_blocked INTEGER DEFAULT 0
                )
            ''')
            
            # جدول اشتراک‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    user_id INTEGER PRIMARY KEY,
                    subscription_type TEXT DEFAULT 'free',
                    start_date TEXT,
                    expiry_date TEXT,
                    daily_signals_used INTEGER DEFAULT 0,
                    last_signal_date TEXT,
                    payment_id TEXT
                )
            ''')
            
            # جدول سیگنال‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    timestamp TEXT,
                    price REAL,
                    signal TEXT,
                    confidence INTEGER,
                    signal_type TEXT,
                    success INTEGER,
                    profit_loss REAL,
                    ict_score REAL,
                    news_score REAL,
                    technical_score REAL
                )
            ''')
            
            # جدول پرداخت‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    payment_method TEXT,
                    amount REAL,
                    currency TEXT,
                    status TEXT DEFAULT 'pending',
                    payment_id TEXT,
                    transaction_hash TEXT,
                    created_at TEXT,
                    completed_at TEXT,
                    subscription_plan TEXT,
                    vpn_warning_sent INTEGER DEFAULT 0
                )
            ''')
            
            # جدول تبدیل‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversion_events (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    event_type TEXT,
                    timestamp TEXT,
                    converted INTEGER DEFAULT 0,
                    conversion_date TEXT
                )
            ''')
            
            # جدول مدیران
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    created_at TEXT,
                    last_login TEXT
                )
            ''')
            
            # جدول لاگ فعالیت‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    timestamp TEXT,
                    ip_address TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_connection(self):
        """دریافت اتصال به پایگاه داده"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
