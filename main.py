#!/usr/bin/env python3
"""
ICT Trading Oracle Bot
"""

import os
import asyncio
import logging
import signal
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found! Please set it in .env file")
    print("❌ BOT_TOKEN not found! Please add it to .env file")
    exit(1)

# Global application variable for graceful shutdown
application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    welcome_text = f"""
🎪 **Welcome to ICT Trading Oracle Bot**

Hello {user.first_name}! 👋

🎯 **Bot Features:**
👉 Professional ICT Analysis
👉 Gold (XAU/USD) Signals
👉 Advanced AI Integration

📊 **Commands:**
/help - Complete guide
/signal - Get trading signal
/price - Current gold price

💎 **Your bot is ready!**
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
🔧 **ICT Trading Oracle Bot Guide**

📋 **Available Commands:**
/start - Start the bot
/help - This guide
/signal - Get ICT signal
/price - Current gold price
/status - Bot status

🎪 **About ICT:**
Inner Circle Trading is a professional market analysis methodology.
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Signal command handler"""
    signal_text = """
📊 **ICT Signal - Gold (XAU/USD)**

💰 **Current Price:** $2,350.25
📈 **Change:** +0.85% (+$19.75)

🎯 **Signal:** BUY
🔥 **Confidence:** 87%
⭐ **Quality:** EXCELLENT

📋 **ICT Analysis:**
👉 Market Structure: BULLISH
👉 Order Block: Confirmed
👉 Fair Value Gap: Active

💡 **Entry:** $2,348.00
🛡️ **Stop Loss:** $2,335.00
🎯 **Take Profit:** $2,365.00

⚠️ **Note:** This is a test signal!
    """
    
    await update.message.reply_text(signal_text, parse_mode='Markdown')

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Price command handler"""
    price_text = """
💰 **Live Gold Price (XAU/USD)**

📊 **$2,350.25**
📈 **Change:** +$19.75 (+0.85%)

⏰ **Last Update:** 2 minutes ago
📅 **Date:** 2025/05/28

🔄 **Refresh:** /price
    """
    
    await update.message.reply_text(price_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command handler"""
    status_text = """
🤖 **ICT Trading Oracle Bot Status**

✅ **Bot:** Active and Ready
✅ **Server:** Connected
✅ **Database:** Active

📊 **Statistics:**
📋 Active Users: 1,250
📈 Today's Signals: 23
🕛 Uptime: 99.9%

🕒 **Server Time:** UTC
    """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global application
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    if application:
        # Stop the application gracefully
        asyncio.create_task(application.stop())
        asyncio.create_task(application.shutdown())
    sys.exit(0)

async def main():
    """Main function"""
    global application
    
    try:
        print("🚀 Starting ICT Trading Oracle Bot...")
        
        # Create Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("signal", signal_command))
        application.add_handler(CommandHandler("price", price_command))
        application.add_handler(CommandHandler("status", status_command))
        
        logger.info("🤖 ICT Trading Oracle Bot starting...")
        print("✅ Bot handlers registered successfully!")
        print("🔄 Starting polling...")
        
        # Initialize the application
        await application.initialize()
        
        # Start the application
        await application.start()
        
        # Start polling
        await application.updater.start_polling()
        
        print("✅ Bot is now running! Press Ctrl+C to stop.")
        
        # Keep the bot running
        try:
            # Run forever
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Received keyboard interrupt, shutting down...")
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"❌ Error: {e}")
    finally:
        # Graceful shutdown
        if application:
            try:
                print("🔄 Shutting down bot...")
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                print("✅ Bot shutdown completed")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

def run_bot():
    """Run the bot with proper event loop handling"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new task
            import nest_asyncio
            nest_asyncio.apply()
            loop.run_until_complete(main())
        else:
            # If no loop is running, use asyncio.run
            asyncio.run(main())
    except RuntimeError as e:
        if "running event loop" in str(e):
            # Alternative method for running event loop
            try:
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(main())
            except ImportError:
                # If nest_asyncio is not available, use basic approach
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(main())
                finally:
                    loop.close()
        else:
            raise
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    run_bot()
