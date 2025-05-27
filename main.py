# Main Application Entry Point 
#!/usr/bin/env python3
"""
Ultimate ICT Trading Bot
Main entry point for the application
"""

import asyncio
import logging
from telegram.ext import Application

from config.settings import BOT_TOKEN
from telegram_bot.handlers import setup_handlers
from core.signal_generator import SignalGenerator
from subscription.manager import SubscriptionManager
from utils.logger import setup_logging
from admin.admin_panel import app as admin_app
import threading

# تنظیم logging
setup_logging()
logger = logging.getLogger(__name__)

class ICTTradingBotApp:
    """کلاس اصلی اپلیکیشن"""
    
    def __init__(self):
        self.application = None
        self.signal_generator = SignalGenerator()
        self.subscription_manager = SubscriptionManager()
        
    async def initialize(self):
        """راه‌اندازی اولیه"""
        try:
            # ایجاد Application
            self.application = Application.builder().token(BOT_TOKEN).build()
            
            # تنظیم handlers
            setup_handlers(self.application, self.signal_generator, self.subscription_manager)
            
            # راه‌اندازی سیستم‌های پس‌زمینه
            await self.signal_generator.initialize()
            
            logger.info("🤖 ICT Trading Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
            raise
    
    async def start(self):
        """شروع ربات"""
        try:
            await self.initialize()
            
            # شروع admin panel در thread جداگانه
            admin_thread = threading.Thread(target=lambda: admin_app.run(host='0.0.0.0', port=5000, debug=False))
            admin_thread.daemon = True
            admin_thread.start()
            
            # شروع polling
            logger.info("🚀 Starting ICT Trading Bot...")
            await self.application.run_polling(allowed_updates=['message', 'callback_query'])
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def stop(self):
        """توقف ربات"""
        try:
            if self.signal_generator:
                await self.signal_generator.stop()
            
            logger.info("🛑 ICT Trading Bot stopped")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

async def main():
    """تابع اصلی"""
    bot_app = ICTTradingBotApp()
    
    try:
        await bot_app.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot_app.stop()

if __name__ == "__main__":
    print("🤖 ICT Trading Bot Starting...")
    print("🌐 Admin Panel: http://localhost:5000/admin")
    asyncio.run(main())
