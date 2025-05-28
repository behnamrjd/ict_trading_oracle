"""
Database Manager for ICT Trading Oracle
"""

import sqlite3
import os
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / "data" / "ict_trading.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        subscription_type TEXT DEFAULT 'free',
                        subscription_expires DATETIME,
                        daily_signals_used INTEGER DEFAULT 0,
                        total_signals_received INTEGER DEFAULT 0,
                        joined_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Signals table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        signal_type TEXT NOT NULL,
                        symbol TEXT DEFAULT 'GOLD',
                        price REAL,
                        signal_direction TEXT,
                        confidence REAL,
                        entry_price REAL,
                        stop_loss REAL,
                        take_profit REAL,
                        market_structure TEXT,
                        order_block TEXT,
                        fvg_status TEXT,
                        rsi_value REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # User signals (tracking which user received which signal)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        signal_id INTEGER,
                        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (signal_id) REFERENCES signals (id)
                    )
                ''')
                
                # Bot statistics
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bot_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        total_users INTEGER DEFAULT 0,
                        active_users INTEGER DEFAULT 0,
                        total_signals INTEGER DEFAULT 0,
                        daily_signals INTEGER DEFAULT 0,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User activity log
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        command TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """Add new user or update existing user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    # Update existing user
                    cursor.execute('''
                        UPDATE users 
                        SET username = ?, first_name = ?, last_name = ?, last_activity = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (username, first_name, last_name, user_id))
                else:
                    # Add new user
                    cursor.execute('''
                        INSERT INTO users (user_id, username, first_name, last_name)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, username, first_name, last_name))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def can_receive_signal(self, user_id):
        """Check if user can receive more signals today"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            # Free users: 3 signals per day
            # Premium users: 50 signals per day  
            # VIP users: unlimited
            
            if user['subscription_type'] == 'vip':
                return True
            
            daily_limit = 50 if user['subscription_type'] == 'premium' else 3
            
            # Reset daily counter if it's a new day
            today = datetime.now().date()
            last_activity = datetime.fromisoformat(user['last_activity']).date()
            
            if today > last_activity:
                self.reset_daily_signals(user_id)
                return True
            
            return user['daily_signals_used'] < daily_limit
            
        except Exception as e:
            logger.error(f"Error checking signal limit: {e}")
            return False
    
    def reset_daily_signals(self, user_id):
        """Reset daily signal counter"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET daily_signals_used = 0 WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error resetting daily signals: {e}")
    
    def add_signal(self, signal_data):
        """Add new signal to database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO signals (
                        signal_type, symbol, price, signal_direction, confidence,
                        entry_price, stop_loss, take_profit, market_structure,
                        order_block, fvg_status, rsi_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal_data.get('signal_type', 'ICT'),
                    signal_data.get('symbol', 'GOLD'),
                    signal_data.get('price'),
                    signal_data.get('signal_direction'),
                    signal_data.get('confidence'),
                    signal_data.get('entry_price'),
                    signal_data.get('stop_loss'),
                    signal_data.get('take_profit'),
                    signal_data.get('market_structure'),
                    signal_data.get('order_block'),
                    signal_data.get('fvg_status'),
                    signal_data.get('rsi_value')
                ))
                
                signal_id = cursor.lastrowid
                conn.commit()
                return signal_id
        except Exception as e:
            logger.error(f"Error adding signal: {e}")
            return None
    
    def record_user_signal(self, user_id, signal_id):
        """Record that user received a signal"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Add to user_signals table
                cursor.execute(
                    "INSERT INTO user_signals (user_id, signal_id) VALUES (?, ?)",
                    (user_id, signal_id)
                )
                
                # Update user's signal counters
                cursor.execute('''
                    UPDATE users 
                    SET daily_signals_used = daily_signals_used + 1,
                        total_signals_received = total_signals_received + 1,
                        last_activity = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id,))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording user signal: {e}")
            return False
    
    def log_user_activity(self, user_id, command):
        """Log user activity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO user_activity (user_id, command) VALUES (?, ?)",
                    (user_id, command)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging user activity: {e}")
    
    def get_bot_stats(self):
        """Get bot statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total users
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
                
                # Active users (last 7 days)
                week_ago = datetime.now() - timedelta(days=7)
                cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE last_activity > ?",
                    (week_ago.isoformat(),)
                )
                active_users = cursor.fetchone()[0]
                
                # Total signals
                cursor.execute("SELECT COUNT(*) FROM signals")
                total_signals = cursor.fetchone()[0]
                
                # Today's signals
                today = datetime.now().date()
                cursor.execute(
                    "SELECT COUNT(*) FROM signals WHERE DATE(created_at) = ?",
                    (today.isoformat(),)
                )
                daily_signals = cursor.fetchone()[0]
                
                return {
                    'total_users': total_users,
                    'active_users': active_users,
                    'total_signals': total_signals,
                    'daily_signals': daily_signals
                }
        except Exception as e:
            logger.error(f"Error getting bot stats: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'total_signals': 0,
                'daily_signals': 0
            }
    
    def get_user_list(self, limit=50):
        """Get list of users for admin"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, first_name, subscription_type, 
                           total_signals_received, last_activity
                    FROM users 
                    ORDER BY last_activity DESC 
                    LIMIT ?
                ''', (limit,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user list: {e}")
            return []
    
    def upgrade_user_subscription(self, user_id, subscription_type, days=30):
        """Upgrade user subscription"""
        try:
            expires_date = datetime.now() + timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET subscription_type = ?, subscription_expires = ?
                    WHERE user_id = ?
                ''', (subscription_type, expires_date.isoformat(), user_id))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            return False
