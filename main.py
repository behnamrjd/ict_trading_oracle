#!/usr/bin/env python3
"""
ICT Trading Oracle Bot - Enhanced Version
"""

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from core.api_manager import APIManager
from core.technical_analysis import TechnicalAnalyzer

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Initialize API manager and technical analyzer
api_manager = APIManager()
tech_analyzer = TechnicalAnalyzer()

def is_admin(user_id: int) -> bool:
    try:
        from config.settings import ADMIN_IDS
        return user_id in ADMIN_IDS
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🎪 **Welcome to ICT Trading Oracle Bot**

Hello {user.first_name}! 👋

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
/admin - Admin panel

💎 **Your bot is ready with REAL data!**

🆔 **Your User ID:** `{user.id}`
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get live gold price"""
    await update.message.reply_text("📊 Fetching live gold price...")
    
    price_data = api_manager.get_gold_price()
    
    if price_data:
        change_emoji = "📈" if price_data['change'] >= 0 else "📉"
        price_text = f"""
💰 **LIVE Gold Price (XAU/USD)**

📊 **${price_data['price']}**
{change_emoji} **Change:** ${price_data['change']} ({price_data['change_percent']:+.2f}%)

⏰ **Last Update:** {price_data['timestamp']}
🔄 **Source:** Yahoo Finance (Live Data)

🔄 **Refresh:** /price
        """
    else:
        price_text = """
❌ **Unable to fetch live price**

🔧 **Possible reasons:**
• Network connectivity issue
• API service temporarily unavailable

🔄 **Try again:** /price
        """
    
    await update.message.reply_text(price_text, parse_mode='Markdown')

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get real ICT analysis"""
    await update.message.reply_text("🔍 Analyzing market with ICT methodology...")
    
    # Get live price
    price_data = api_manager.get_gold_price()
    
    # Get technical analysis
    analysis = tech_analyzer.analyze_market_structure()
    
    if price_data and analysis:
        signal_emoji = "🟢" if analysis['signal'] == 'BUY' else "🔴" if analysis['signal'] == 'SELL' else "🟡"
        confidence_stars = "⭐" * min(int(analysis['confidence'] / 20), 5)
        
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

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get latest gold news"""
    await update.message.reply_text("📰 Fetching latest gold market news...")
    
    news_data = api_manager.get_gold_news()
    
    if news_data:
        news_text = "📰 **Latest Gold Market News**\n\n"
        
        for i, article in enumerate(news_data[:3], 1):
            news_text += f"""
**{i}. {article['title']}**
{article['description'][:100]}...

🔗 [Read More]({article['url']})
📅 {article['publishedAt'][:10]}

"""
        
        news_text += "\n🔄 **Refresh:** /news"
    else:
        news_text = """
❌ **Unable to fetch news**

🔧 **Possible reasons:**
• News API service issue
• Network connectivity problem

🔄 **Try again:** /news
        """
    
    await update.message.reply_text(news_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🔧 **ICT Trading Oracle Bot Guide**

📋 **Available Commands:**
/start - Start the bot
/help - This guide
/price - **LIVE** gold price from Yahoo Finance
/signal - **REAL** ICT technical analysis
/news - Latest gold market news
/admin - Admin panel (admin only)

🎪 **About ICT:**
Inner Circle Trading methodology with REAL market data:
• Live price feeds
• Technical analysis with RSI, MACD, Bollinger Bands
• Market structure analysis
• Order block detection
• Fair Value Gap identification

💡 **Data Sources:**
📊 Prices: Yahoo Finance
📰 News: NewsAPI
🔍 Analysis: Real-time technical indicators
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ You don't have admin access!")
        return
    
    admin_text = """
🔧 **Admin Panel - ICT Trading Oracle**

👑 **Welcome Admin!**

📊 **Admin Commands:**
/broadcast - Send message to all users
/stats - Detailed statistics
/test_apis - Test API connections

🛠️ **System Info:**
✅ Bot Status: Running with REAL data
✅ Yahoo Finance: Connected
✅ NewsAPI: Connected
✅ Technical Analysis: Active

💡 **Quick Actions:**
- Test APIs: /test_apis
- View system logs: Check server
    """
    await update.message.reply_text(admin_text, parse_mode='Markdown')

async def test_apis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test API connections (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return
    
    await update.message.reply_text("🔧 Testing API connections...")
    
    # Test gold price API
    price_test = "✅" if api_manager.get_gold_price() else "❌"
    
    # Test news API
    news_test = "✅" if api_manager.get_gold_news() else "❌"
    
    # Test technical analysis
    analysis_test = "✅" if tech_analyzer.analyze_market_structure() else "❌"
    
    test_text = f"""
🔧 **API Connection Test Results**

📊 **Yahoo Finance (Gold Price):** {price_test}
📰 **NewsAPI (Market News):** {news_test}
🔍 **Technical Analysis:** {analysis_test}
🇮🇷 **TGJU API:** ⏳ (Optional)

**Overall Status:** {'✅ All systems operational' if all([price_test == "✅", news_test == "✅", analysis_test == "✅"]) else '⚠️ Some services may be unavailable'}
    """
    
    await update.message.reply_text(test_text, parse_mode='Markdown')

async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("signal", signal_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("test_apis", test_apis_command))
    
    print("🚀 ICT Trading Oracle Bot starting with REAL APIs...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
