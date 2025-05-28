#!/usr/bin/env python3
"""
ICT Trading Oracle Bot - Enhanced Version with Database
"""

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from core.api_manager import APIManager
from core.technical_analysis import TechnicalAnalyzer
from core.database import DatabaseManager

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Initialize managers
api_manager = APIManager()
tech_analyzer = TechnicalAnalyzer()
db_manager = DatabaseManager()

def is_admin(user_id: int) -> bool:
    try:
        from config.settings import ADMIN_IDS
        return user_id in ADMIN_IDS
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Add user to database
    db_manager.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Log activity
    db_manager.log_user_activity(user.id, '/start')
    
    # Get user info from database
    user_data = db_manager.get_user(user.id)
    subscription = user_data['subscription_type'] if user_data else 'free'
    
    welcome_text = f"""
🎪 **Welcome to ICT Trading Oracle Bot**

Hello {user.first_name}! 👋

🎯 **Your Subscription:** {subscription.upper()}
📊 **Signals Used Today:** {user_data['daily_signals_used'] if user_data else 0}

🎯 **Bot Features:**
👉 **LIVE** Gold Price Data
👉 **REAL** ICT Technical Analysis  
👉 **LIVE** Market News
👉 Professional Trading Signals

📊 **Commands:**
/help - Complete guide
/price - **LIVE** gold price
/signal - **REAL** ICT analysis
/news - Latest gold news
/profile - Your profile & stats
/admin - Admin panel

💎 **Your bot is ready with REAL data!**

🆔 **Your User ID:** `{user.id}`
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get real ICT analysis with database tracking"""
    user_id = update.effective_user.id
    
    # Log activity
    db_manager.log_user_activity(user_id, '/signal')
    
    # Check if user can receive signals
    if not db_manager.can_receive_signal(user_id):
        user_data = db_manager.get_user(user_id)
        limit = 3 if user_data['subscription_type'] == 'free' else 50
        
        await update.message.reply_text(f"""
⚠️ **Daily Signal Limit Reached**

You've used all {limit} signals for today.

🔄 **Reset Time:** Tomorrow at 00:00 UTC
💎 **Upgrade:** Contact admin for premium subscription

📊 **Current Plan:** {user_data['subscription_type'].upper()}
        """, parse_mode='Markdown')
        return
    
    await update.message.reply_text("🔍 Analyzing market with ICT methodology...")
    
    # Get live price and analysis
    price_data = api_manager.get_gold_price()
    analysis = tech_analyzer.analyze_market_structure()
    
    if price_data and analysis:
        # Save signal to database
        signal_data = {
            'signal_type': 'ICT',
            'symbol': 'GOLD',
            'price': price_data['price'],
            'signal_direction': analysis['signal'],
            'confidence': analysis['confidence'],
            'entry_price': price_data['price'],
            'stop_loss': price_data['price'] * 0.99,  # 1% stop loss
            'take_profit': price_data['price'] * 1.02,  # 2% take profit
            'market_structure': analysis['market_structure'],
            'order_block': analysis['order_block'],
            'fvg_status': analysis['fvg_status'],
            'rsi_value': analysis['rsi']
        }
        
        signal_id = db_manager.add_signal(signal_data)
        if signal_id:
            db_manager.record_user_signal(user_id, signal_id)
        
        signal_emoji = "🟢" if analysis['signal'] == 'BUY' else "🔴" if analysis['signal'] == 'SELL' else "🟡"
        confidence_stars = "⭐" * min(int(analysis['confidence'] / 20), 5)
        
        # Get updated user stats
        user_data = db_manager.get_user(user_id)
        
        signal_text = f"""
📊 **REAL ICT Analysis - Gold (XAU/USD)**

💰 **Current Price:** ${price_data['price']}
📈 **Change:** ${price_data['change']} ({price_data['change_percent']:+.2f}%)

{signal_emoji} **Signal:** {analysis['signal']}
🔥 **Confidence:** {analysis['confidence']}%
{confidence_stars} **Quality:** {'EXCELLENT' if analysis['confidence'] > 80 else 'GOOD' if analysis['confidence'] > 60 else 'FAIR'}

📋 **ICT Analysis:**
👉 Market Structure: {analysis['market_structure']}
👉 Order Block: {analysis['order_block']}
👉 Fair Value Gap: {analysis['fvg_status']}
👉 RSI: {analysis['rsi']}

💡 **Entry:** ${signal_data['entry_price']}
🛡️ **Stop Loss:** ${signal_data['stop_loss']:.2f}
🎯 **Take Profit:** ${signal_data['take_profit']:.2f}

📊 **Your Stats:**
🔢 Signals Used Today: {user_data['daily_signals_used']}/{'∞' if user_data['subscription_type'] == 'vip' else '50' if user_data['subscription_type'] == 'premium' else '3'}
📈 Total Signals: {user_data['total_signals_received']}

⏰ **Analysis Time:** {analysis['analysis_time']}
🔄 **Refresh:** /signal

⚠️ **Note:** Based on real market data and technical analysis!
        """
    else:
        signal_text = """
❌ **Unable to generate analysis**

🔧 **Possible reasons:**
• Market data unavailable
• Technical analysis service issue

🔄 **Try again:** /signal
        """
    
    await update.message.reply_text(signal_text, parse_mode='Markdown')

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile and statistics"""
    user_id = update.effective_user.id
    
    # Log activity
    db_manager.log_user_activity(user_id, '/profile')
    
    user_data = db_manager.get_user(user_id)
    
    if user_data:
        subscription_emoji = "💎" if user_data['subscription_type'] == 'vip' else "⭐" if user_data['subscription_type'] == 'premium' else "🆓"
        
        profile_text = f"""
👤 **Your Profile - ICT Trading Oracle**

{subscription_emoji} **Subscription:** {user_data['subscription_type'].upper()}
📅 **Member Since:** {user_data['joined_date'][:10]}
🕐 **Last Activity:** {user_data['last_activity'][:16]}

📊 **Signal Statistics:**
🔢 **Today's Signals:** {user_data['daily_signals_used']}/{'∞' if user_data['subscription_type'] == 'vip' else '50' if user_data['subscription_type'] == 'premium' else '3'}
📈 **Total Signals:** {user_data['total_signals_received']}

💡 **Subscription Benefits:**
{'🔓 Unlimited daily signals' if user_data['subscription_type'] == 'vip' else '🔓 50 daily signals' if user_data['subscription_type'] == 'premium' else '🔒 3 daily signals (upgrade for more)'}
{'🔓 Premium analysis' if user_data['subscription_type'] != 'free' else '🔒 Premium analysis (upgrade required)'}
{'🔓 Priority support' if user_data['subscription_type'] == 'vip' else '🔒 Priority support (VIP only)'}

🆔 **User ID:** `{user_id}`
        """
    else:
        profile_text = "❌ Profile not found. Please use /start first."
    
    await update.message.reply_text(profile_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return
    
    stats = db_manager.get_bot_stats()
    
    stats_text = f"""
📊 **Bot Statistics - ICT Trading Oracle**

👥 **Users:**
📋 Total Users: {stats['total_users']}
🟢 Active Users (7 days): {stats['active_users']}

📈 **Signals:**
📊 Total Signals: {stats['total_signals']}
📅 Today's Signals: {stats['daily_signals']}

💡 **Performance:**
📈 Avg Signals/User: {stats['total_signals'] / max(stats['total_users'], 1):.1f}
🎯 Active Rate: {(stats['active_users'] / max(stats['total_users'], 1) * 100):.1f}%
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user list (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return
    
    users = db_manager.get_user_list(20)
    
    if users:
        users_text = "👥 **Recent Users (Last 20)**\n\n"
        
        for user in users:
            subscription_emoji = "💎" if user['subscription_type'] == 'vip' else "⭐" if user['subscription_type'] == 'premium' else "🆓"
            users_text += f"""
{subscription_emoji} **{user['first_name'] or 'Unknown'}** (@{user['username'] or 'no_username'})
🆔 ID: `{user['user_id']}`
📊 Signals: {user['total_signals_received']}
🕐 Last: {user['last_activity'][:10]}

"""
        
        users_text += f"\n📋 **Total:** {len(users)} users shown"
    else:
        users_text = "❌ No users found."
    
    await update.message.reply_text(users_text, parse_mode='Markdown')

# اضافه کردن handlers جدید به main function
async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("signal", signal_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("test_apis", test_apis_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("users", users_command))
    
    print("🚀 ICT Trading Oracle Bot starting with Database + APIs...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
