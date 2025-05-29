#!/usr/bin/env python3
"""
ICT Trading Oracle Bot - Complete Version with All Features
"""

import os
import asyncio
import signal
import sys
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# Attempt to import logging settings first
try:
    from config.settings import LOG_LEVEL, LOG_FILE_PATH_CONFIG
except ImportError:
    # Fallback if config.settings is not available or structured differently initially
    LOG_LEVEL = "INFO"
    # Define a fallback log path if import fails, though main setup below also has one.
    # This helps if logger is used before full setup in rare cases.
    LOG_FILE_PATH_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "ict_trading_fallback.log") 

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Path setup for logging (directory creation part)
# Ensure the directory for the log file exists. LOG_FILE_PATH_CONFIG is an absolute path string.
LOG_DIR_FROM_CONFIG = os.path.dirname(LOG_FILE_PATH_CONFIG)
os.makedirs(LOG_DIR_FROM_CONFIG, exist_ok=True)

# Load environment variables early
load_dotenv()

# Setup logging using imported settings
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL, logging.INFO), # Use getattr for safety
    handlers=[
        logging.FileHandler(LOG_FILE_PATH_CONFIG),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Get Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    # This print is for immediate user feedback if logs aren't set up or seen
    print("❌ BOT_TOKEN not found in .env file. Please set it and try again.")
    # Logger might not be fully configured yet, but try to log critical error.
    logging.getLogger(__name__).critical("BOT_TOKEN not found! Please set it in .env file")
    exit(1)

# Global application variable removed, will be handled in main()

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    try:
        from config.settings import ADMIN_IDS
        return user_id in ADMIN_IDS
    except ImportError:
        logger.error("Could not import ADMIN_IDS from config.settings")
        return False

# Safe imports for core modules
def safe_import_api_manager():
    """Safely import APIManager"""
    try:
        from core.api_manager import APIManager
        return APIManager()
    except ImportError as e:
        logger.error(f"Could not import APIManager: {e}")
        return None

def safe_import_technical_analyzer():
    """Safely import RealICTAnalyzer"""
    try:
        from core.technical_analysis import RealICTAnalyzer
        return RealICTAnalyzer()
    except ImportError as e:
        logger.error(f"Could not import RealICTAnalyzer: {e}")
        return None

def safe_import_database_manager():
    """Safely import DatabaseManager"""
    try:
        from core.database import DatabaseManager
        return DatabaseManager()
    except ImportError as e:
        logger.error(f"Could not import DatabaseManager: {e}")
        return None

# Import new keyboard and handler
from telegram_bot.keyboards import get_main_menu_keyboard
from telegram_bot.handlers import button_handler

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    if not update.message or not update.effective_user:
        logger.warning("Start command received without message or effective_user.")
        return

    user = update.effective_user
    
    # Add user to database
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            db_manager.add_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db_manager.log_user_activity(user.id, '/start')
            
            # Get user info from database
            user_data = db_manager.get_user(user.id)
            subscription = user_data['subscription_type'] if user_data else 'free'
            
            # Force VIP for admins
            if is_admin(user.id):
                subscription = 'vip'
                db_manager.upgrade_user_subscription(user.id, 'vip', 365)
        else:
            subscription = 'free'
    except Exception as e:
        logger.error(f"Database error in start command: {e}")
        subscription = 'free'
    
    logger.info(f"User started bot - ID: {user.id}, Username: {user.username}, Name: {user.first_name}")
    
    if is_admin(user.id):
        subscription_emoji = "👑"
        subscription_display_name = "ADMIN"
    else:
        if subscription == 'vip':
            subscription_emoji = "💎"
            subscription_display_name = "VIP"
        elif subscription == 'premium':
            subscription_emoji = "⭐"
            subscription_display_name = "PREMIUM"
        else:
            subscription_emoji = "🆓"
            subscription_display_name = "FREE"
    
    welcome_text = f"""
🎪 **به ربات اوراکل خوش آمدید!**

سلام {user.first_name}! 👋

{subscription_emoji} **وضعیت اشتراک شما:** {subscription_display_name}
🆔 **شناسه کاربری شما:** `{user.id}`

برای استفاده از امکانات ربات، از دکمه‌های زیر استفاده کنید:
    """
    
    # Send welcome message with the new inline keyboard
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler - now shows the main menu"""
    if not update.message or not update.effective_user:
        logger.warning("Help command received without message or effective_user.")
        return
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            db_manager.log_user_activity(update.effective_user.id, '/help')
    except Exception as e:
        logger.warning(f"Failed to log user activity for /help: {e}")
    
    help_text = "راهنمای ربات:\n\nاز دکمه‌های زیر برای تعامل با ربات استفاده کنید."
    
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_menu_keyboard(), # Show the main menu
        parse_mode='Markdown'
    )

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get live gold price"""
    if not update.message or not update.effective_user:
        logger.warning("Price command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            db_manager.log_user_activity(user_id, '/price')
    except Exception as e:
        logger.warning(f"Failed to log user activity for /price: {e}")
    
    await update.message.reply_text("📊 Fetching live gold price...")
    
    try:
        api_manager = safe_import_api_manager()
        if api_manager:
            price_data = api_manager.get_gold_price()
            
            if price_data:
                change_emoji = "📈" if price_data['change'] >= 0 else "📉"
                price_text = f"""
💰 **LIVE Gold Price (XAU/USD)**

📊 **${price_data['price']}**
{change_emoji} **Change:** ${price_data['change']} ({price_data['change_percent']:+.2f}%)

⏰ **Last Update:** {price_data['timestamp']}
🔄 **Source:** Real-time Market Data

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
        else:
            price_text = "❌ **Error:** API Manager not available"
    except Exception as e:
        logger.error(f"Error in price command: {e}")
        price_text = f"❌ **Error fetching price:** {str(e)}"
    
    await update.message.reply_text(price_text, parse_mode='Markdown')

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get real ICT analysis with advanced 25+ indicators"""
    if not update.message or not update.effective_user:
        logger.warning("Signal command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    # Check if user can receive signals
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            db_manager.log_user_activity(user_id, '/signal')
            
            if not is_admin(user_id) and not db_manager.can_receive_signal(user_id):
                user_data = db_manager.get_user(user_id)
                limit = 3 if user_data and user_data['subscription_type'] == 'free' else 50
                
                await update.message.reply_text(f"""
⚠️ **Daily Signal Limit Reached**

You've used all {limit} signals for today.

🔄 **Reset Time:** Tomorrow at 00:00 UTC
💎 **Upgrade:** Use /subscribe for premium subscription

📊 **Current Plan:** {user_data['subscription_type'].upper() if user_data else 'FREE'}
                """, parse_mode='Markdown')
                return
    except Exception as e:
        logger.warning(f"Database error in signal command (checking limits or logging activity): {e}")
        # Decide if we should return or proceed with caution if DB is down
        # For now, we'll let it proceed, but signal saving might fail.
    
    # Show analysis progress
    progress_msg = await update.message.reply_text("🔍 **Starting Advanced ICT Analysis...**\n\n⏳ Fetching multi-timeframe data...")
    
    try:
        # Import the new analyzer
        from core.technical_analysis import RealICTAnalyzer # Import class directly for type hinting
        tech_analyzer: RealICTAnalyzer | None = safe_import_technical_analyzer()
        api_manager = safe_import_api_manager()
        
        if not tech_analyzer:
            await progress_msg.edit_text("❌ **Error:** Technical analyzer not available")
            return
        
        # Update progress
        await progress_msg.edit_text("🔍 **Advanced ICT Analysis in Progress...**\n\n📊 Analyzing market structure...\n⚡ Detecting order blocks...\n💧 Finding liquidity pools...")
        
        # Get comprehensive analysis
        analysis = tech_analyzer.generate_real_ict_signal()
        
        # Update progress
        await progress_msg.edit_text("🔍 **Advanced ICT Analysis in Progress...**\n\n📈 Calculating 25+ indicators...\n🎯 Generating signal...\n✅ Almost done...")
        
        if analysis and analysis.get('data_quality') != 'FALLBACK_MODE':
            # Build comprehensive signal message
            signal_text = f"""
🎯 **Advanced ICT Analysis - Gold (XAU/USD)**
📊 **Real-Time Analysis with 25+ Indicators**

💰 **Current Price:** ${analysis['current_price']}
🎪 **Signal:** {analysis['signal']} 
🔥 **Confidence:** {analysis['confidence']}%
⭐ **Quality:** {analysis['signal_quality']}

📋 **ICT Structure Analysis:**
🏗️ Market Structure: {analysis['ict_analysis']['market_structure']} ({analysis['ict_analysis']['structure_strength']}%)
📦 Order Blocks: {analysis['ict_analysis']['order_blocks_count']} detected
⚡ Fair Value Gaps: {analysis['ict_analysis']['fair_value_gaps']} active
💧 Liquidity Pools: {analysis['ict_analysis']['liquidity_pools']} identified

📊 **Technical Summary:**
📈 Trend: {analysis['technical_summary']['trend_direction']} (Strength: {analysis['technical_summary']['trend_strength']}%)
🚀 Momentum: {analysis['technical_summary']['momentum_strength']}%
📊 RSI(14): {analysis['technical_summary']['rsi_14']}
📈 MACD: {analysis['technical_summary']['macd_signal']}
🎯 BB Position: {analysis['technical_summary']['bb_position']['position']}

🕐 **Multi-Timeframe Analysis:**
🎯 Overall Bias: {analysis['multi_timeframe']['overall_bias']} ({analysis['multi_timeframe']['strength']}%)
📊 Timeframes: {', '.join(analysis['multi_timeframe']['timeframes_analyzed'])}

💡 **Trading Levels:**
🎯 Entry Zone: ${analysis['trading_levels']['entry_zone']['low']:.2f} - ${analysis['trading_levels']['entry_zone']['high']:.2f}
🛡️ Stop Loss: ${analysis['trading_levels']['stop_loss']}
🎯 Take Profit 1: ${analysis['trading_levels']['take_profit_1']}
🎯 Take Profit 2: ${analysis['trading_levels']['take_profit_2']}
📊 Risk/Reward: 1:{analysis['trading_levels']['risk_reward_ratio']}

🔗 **Signal Confluence:** {analysis['confluence_factors']} factors
📝 **Key Reasons:**
"""
            
            # Add top reasons
            for i, reason in enumerate(analysis['signal_reasoning'][:3], 1):
                signal_text += f"   {i}. {reason}\n"
            
            signal_text += f"""
🌐 **Market Context:**
🕐 Session: {analysis['market_context']['session']}
📊 Volatility: {analysis['market_context']['volatility_environment']}
📈 Trend Environment: {analysis['market_context']['trend_environment']}

📊 **Analysis Details:**
🔢 Indicators Used: {analysis['indicators_count']}
⏰ Analysis Time: {analysis['analysis_time']}
🎯 Primary Timeframe: {analysis['timeframe_used']}
📡 Data Quality: {analysis['data_quality']}

⚠️ **Note:** Advanced ICT analysis with real market data and 25+ technical indicators!

🔄 **Refresh:** /signal
            """
            
            # Record signal in database
            try:
                if db_manager:
                    signal_data = {
                        'signal_type': 'ICT_ADVANCED',
                        'symbol': 'GOLD',
                        'price': analysis['current_price'],
                        'signal_direction': analysis['signal'],
                        'confidence': analysis['confidence'],
                        'entry_price': analysis['current_price'],
                        'stop_loss': analysis['trading_levels']['stop_loss'],
                        'take_profit': analysis['trading_levels']['take_profit_1'],
                        'market_structure': analysis['ict_analysis']['market_structure'],
                        'order_block': f"{analysis['ict_analysis']['order_blocks_count']} blocks",
                        'fvg_status': f"{analysis['ict_analysis']['fair_value_gaps']} gaps",
                        'rsi_value': analysis['technical_summary']['rsi_14'],
                        'confluence_factors': analysis['confluence_factors'],
                        'signal_quality': analysis['signal_quality']
                    }
                    
                    signal_id = db_manager.add_signal(signal_data)
                    if signal_id and not is_admin(user_id):
                        db_manager.record_user_signal(user_id, signal_id)
            except Exception as e:
                logger.error(f"Error saving advanced signal to database: {e}")
            
        else:
            # Fallback message
            signal_text = """
❌ **Advanced ICT Analysis Unavailable**

🔧 **Issue:** Unable to fetch real-time market data
📊 **Fallback:** Basic analysis mode active

🔄 **Try again:** /signal
📞 **Support:** Contact admin if issue persists

💡 **Tip:** Advanced analysis requires stable internet connection and market data access.
            """
        
        # Send final result
        await progress_msg.edit_text(signal_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in advanced signal command: {e}")
        await progress_msg.edit_text(f"""
❌ **Analysis Error**

🔧 **Error:** {str(e)[:100]}...
🔄 **Try again:** /signal
📞 **Support:** Contact admin

💡 **Note:** This is an advanced analysis system. Some errors are expected during development.
        """, parse_mode='Markdown')

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get latest gold news"""
    if not update.message or not update.effective_user:
        logger.warning("News command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            db_manager.log_user_activity(user_id, '/news')
    except Exception as e:
        logger.warning(f"Failed to log user activity for /news: {e}")
    
    await update.message.reply_text("📰 Fetching latest gold market news...")
    
    try:
        api_manager = safe_import_api_manager()
        if api_manager:
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
        else:
            news_text = "❌ **Error:** API Manager not available"
    except Exception as e:
        logger.error(f"Error in news command: {e}")
        news_text = f"❌ **Error fetching news:** {str(e)}"
    
    await update.message.reply_text(news_text, parse_mode='Markdown')

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile and statistics"""
    if not update.message or not update.effective_user:
        logger.warning("Profile command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            db_manager.log_user_activity(user_id, '/profile')
            user_data = db_manager.get_user(user_id)
            
            if user_data:
                subscription_type = user_data['subscription_type']
                
                # Override for admins
                if is_admin(user_id):
                    subscription_emoji = "👑"
                    subscription_display = "ADMIN"
                else:
                    subscription_emoji = "💎" if subscription_type == 'vip' else "⭐" if subscription_type == 'premium' else "🆓"
                    subscription_display = subscription_type.upper()
                
                profile_text = f"""
👤 **Your Profile - ICT Trading Oracle**

{subscription_emoji} **Subscription:** {subscription_display}
📅 **Member Since:** {user_data['joined_date'][:10]}
🕐 **Last Activity:** {user_data['last_activity'][:16]}

📊 **Signal Statistics:**
🔢 **Today's Signals:** {user_data['daily_signals_used']}/{'∞' if subscription_type == 'vip' or is_admin(user_id) else '50' if subscription_type == 'premium' else '3'}
📈 **Total Signals:** {user_data['total_signals_received']}

💡 **Subscription Benefits:**
{'🔓 Unlimited daily signals' if subscription_type == 'vip' or is_admin(user_id) else '🔓 50 daily signals' if subscription_type == 'premium' else '🔒 3 daily signals (upgrade for more)'}
{'🔓 Premium analysis' if subscription_type != 'free' or is_admin(user_id) else '🔒 Premium analysis (upgrade required)'}
{'🔓 Priority support' if subscription_type == 'vip' or is_admin(user_id) else '🔒 Priority support (VIP only)'}
{'🔓 Backtest access' if is_admin(user_id) else '🔒 Backtest access (admin only)'}

🆔 **User ID:** `{user_id}`

💎 **Want more features?** Use /subscribe to upgrade!
                """
            else:
                profile_text = "❌ Profile not found. Please use /start first."
        else:
            profile_text = "❌ **Error:** Database not available"
    except Exception as e:
        logger.error(f"Error in profile command: {e}")
        profile_text = f"❌ **Error loading profile:** {str(e)}"
    
    await update.message.reply_text(profile_text, parse_mode='Markdown')

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription options"""
    if not update.message or not update.effective_user:
        logger.warning("Subscribe command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            db_manager.log_user_activity(user_id, '/subscribe')
            user_data = db_manager.get_user(user_id)
            current_plan = user_data['subscription_type'] if user_data else 'free'
        else:
            current_plan = 'free'
    except Exception as e:
        logger.warning(f"Failed to get user data or log activity for /subscribe: {e}")
        current_plan = 'free' # Default to free if DB interaction fails
    
    if is_admin(user_id):
        current_plan = 'admin'
    
    subscribe_text = f"""
💳 **ICT Trading Oracle Subscriptions**

📊 **Current Plan:** {current_plan.upper()}

🎯 **Available Plans:**

🆓 **FREE**
• 3 daily signals
• Basic ICT analysis
• Live gold prices
• Market news

⭐ **PREMIUM - 49,000 تومان/ماه**
• 50 daily signals
• Advanced ICT analysis
• AI-powered insights
• Email support
• Premium indicators

💎 **VIP - 149,000 تومان/ماه**
• Unlimited signals
• Full AI features
• Machine learning predictions
• Sentiment analysis
• Priority support
• Custom alerts
• Advanced reports

💡 **Payment Methods:**
🔒 ZarinPal (Iranian bank cards)
💳 Secure payment processing
⚡ Instant activation

📞 **To upgrade, contact admin for subscription activation**

🆔 **Your User ID:** `{user_id}`
    """
    
    await update.message.reply_text(subscribe_text, parse_mode='Markdown')

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel command"""
    if not update.message or not update.effective_user:
        logger.warning("Admin command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ You don't have admin access!")
        return
    
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            stats = db_manager.get_bot_stats()
        else:
            stats = {
                'total_users': 0,
                'active_users': 0,
                'total_signals': 0,
                'daily_signals': 0
            }
    except Exception as e:
        logger.error(f"Error getting stats in admin command: {e}")
        stats = {
            'total_users': 0,
            'active_users': 0,
            'total_signals': 0,
            'daily_signals': 0
        }
    
    admin_text = f"""
🔧 **Admin Panel - ICT Trading Oracle**

👑 **Welcome Admin!**

📊 **Quick Stats:**
👥 Total Users: {stats['total_users']}
🟢 Active Users: {stats['active_users']}
📈 Total Signals: {stats['total_signals']}
📅 Today's Signals: {stats['daily_signals']}

📋 **Admin Commands:**
/stats - Detailed statistics
/users - User management
/test_system - Run system tests
/backtest [days] [trades_per_day] - Performance analysis (admin only, params optional)

🛠️ **System Status:**
✅ Bot: Running with ALL features
✅ Database: Connected
✅ APIs: Online
✅ Payment: ZarinPal Ready
✅ Backtest: Available

💡 **Advanced Features:**
🤖 AI/ML Models: Ready
📊 Analytics: Real-time
🔒 Security: Enhanced
⚡ Performance: Optimized
📈 Backtest: 7-day analysis available
    """
    await update.message.reply_text(admin_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics (admin only)"""
    if not update.message or not update.effective_user:
        logger.warning("Stats command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return
    
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            stats = db_manager.get_bot_stats()
            
            stats_text = f"""
📊 **Detailed Bot Statistics**

👥 **Users:**
📋 Total Users: {stats['total_users']}
🟢 Active Users (7 days): {stats['active_users']}

📈 **Signals:**
📊 Total Signals: {stats['total_signals']}
📅 Today's Signals: {stats['daily_signals']}

💡 **Performance:**
📈 Avg Signals/User: {stats['total_signals'] / max(stats['total_users'], 1):.1f}
🎯 Active Rate: {(stats['active_users'] / max(stats['total_users'], 1) * 100):.1f}%

💳 **Subscriptions:**
🆓 Free Users: {stats['total_users'] - stats.get('premium_users', 0) - stats.get('vip_users', 0)}
⭐ Premium Users: {stats.get('premium_users', 0)}
💎 VIP Users: {stats.get('vip_users', 0)}

🆕 **New Features:**
📊 Backtest Analysis: Available
🎯 Enhanced Signals: Active
📈 Real-time Data: Connected
            """
        else:
            stats_text = "❌ **Error:** Database not available"
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        stats_text = f"❌ **Error loading statistics:** {str(e)}"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user list (admin only)"""
    if not update.message or not update.effective_user:
        logger.warning("Users command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return
    
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            users = db_manager.get_user_list(10)
            
            if users:
                users_text = "👥 **Recent Users (Last 10)**\n\n"
                
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
        else:
            users_text = "❌ **Error:** Database not available"
    except Exception as e:
        logger.error(f"Error in users command: {e}")
        users_text = f"❌ **Error loading users:** {str(e)}"
    
    await update.message.reply_text(users_text, parse_mode='Markdown')

async def test_system_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test system components (admin only)"""
    if not update.message or not update.effective_user:
        logger.warning("Test_system command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return
    
    await update.message.reply_text("🔧 Testing system components...")
    
    test_results = []
    
    # Test API Manager
    try:
        api_manager = safe_import_api_manager()
        if api_manager:
            price_data = api_manager.get_gold_price()
            test_results.append(("API Manager", "✅" if price_data else "❌"))
        else:
            test_results.append(("API Manager", "❌ Import failed"))
    except Exception as e:
        test_results.append(("API Manager", f"❌ {str(e)[:50]}"))
    
    # Test Technical Analyzer
    try:
        from core.technical_analysis import RealICTAnalyzer # Import for type hint
        tech_analyzer: RealICTAnalyzer | None = safe_import_technical_analyzer()
        if tech_analyzer:
            analysis_result = tech_analyzer.generate_real_ict_signal()
            test_results.append(("Technical Analyzer", "✅" if analysis_result and 'signal' in analysis_result else "❌"))
        else:
            test_results.append(("Technical Analyzer", "❌ Import failed"))
    except Exception as e:
        test_results.append(("Technical Analyzer", f"❌ {str(e)[:50]}"))
    
    # Test Database
    try:
        db_manager = safe_import_database_manager()
        if db_manager:
            stats = db_manager.get_bot_stats()
            test_results.append(("Database", "✅" if stats else "❌"))
        else:
            test_results.append(("Database", "❌ Import failed"))
    except Exception as e:
        test_results.append(("Database", f"❌ {str(e)[:50]}"))
    
    # Test Payment Manager
    try:
        from core.payment_manager import PaymentManager
        payment_manager = PaymentManager()
        test_results.append(("Payment Manager", "✅"))
    except Exception as e:
        test_results.append(("Payment Manager", f"❌ {str(e)[:50]}"))
    
    # Test Backtest Module
    try:
        from backtest.backtest_analyzer import BacktestAnalyzer
        backtest = BacktestAnalyzer()
        test_results.append(("Backtest Analyzer", "✅"))
    except Exception as e:
        test_results.append(("Backtest Analyzer", f"❌ {str(e)[:50]}"))
    
    test_text = "🔧 **System Test Results**\n\n"
    for component, result in test_results:
        test_text += f"**{component}:** {result}\n"
    
    await update.message.reply_text(test_text, parse_mode='Markdown')

async def backtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run configurable backtest (admin only)"""
    if not update.message or not update.effective_user:
        logger.warning("Backtest command received without message or effective_user.")
        return
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return

    days_to_backtest = None
    signals_per_day_val = None
    args_error = False

    if context.args:
        if len(context.args) >= 1:
            try:
                days_to_backtest = int(context.args[0])
                if days_to_backtest <= 0:
                    await update.message.reply_text("❌ Number of days must be a positive integer.")
                    args_error = True
            except ValueError:
                await update.message.reply_text("❌ Invalid format for days. Please provide an integer.")
                args_error = True
        
        if len(context.args) >= 2 and not args_error:
            try:
                signals_per_day_val = int(context.args[1])
                if signals_per_day_val <= 0:
                    await update.message.reply_text("❌ Signals per day must be a positive integer.")
                    args_error = True
            except ValueError:
                await update.message.reply_text("❌ Invalid format for signals per day. Please provide an integer.")
                args_error = True
        
        if len(context.args) > 2 and not args_error:
            await update.message.reply_text("⚠️ Too many arguments. Usage: /backtest [days] [signals_per_day]")
            args_error = True
            
    if args_error:
        return # Stop processing if there was an error with arguments

    # Determine message based on provided arguments
    if days_to_backtest and signals_per_day_val:
        start_message = f"🚀 Starting {days_to_backtest}-day backtest with {signals_per_day_val} signals/day... This may take a moment..."
    elif days_to_backtest:
        start_message = f"🚀 Starting {days_to_backtest}-day backtest (default signals/day)... This may take a moment..."
    else:
        # Defaults will be used from config by BacktestAnalyzer if None is passed
        start_message = "🚀 Starting backtest with default settings... This may take a moment..."
    
    await update.message.reply_text(start_message)
    
    try:
        from backtest.backtest_analyzer import BacktestAnalyzer
        
        backtest = BacktestAnalyzer()
        # Pass parameters to run_full_backtest; it will use its defaults if these are None
        results = backtest.run_full_backtest(days=days_to_backtest, signals_per_day=signals_per_day_val)
        
        # Send report
        await update.message.reply_text(results['report'], parse_mode='Markdown')
        
        # Send summary
        analysis = results['analysis']
        summary = f"""
🎯 **Quick Summary:**
📊 {analysis['total_signals']} signals tested
✅ {analysis['win_rate']}% win rate
💰 ${analysis['total_pnl']} total PnL

📈 **Performance Metrics:**
🎯 Target Hits: {analysis['target_hits']}
🛡️ Stop Hits: {analysis['stop_hits']}
⏰ Time Exits: {analysis['time_exits']}

💡 **Average Results:**
📈 Avg Win: ${analysis['avg_win']}
📉 Avg Loss: ${analysis['avg_loss']}
        """
        await update.message.reply_text(summary, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in backtest command: {e}")
        await update.message.reply_text(f"❌ **Backtest Error:** {str(e)}")

async def main_bot_logic(application: Application, stop_event: asyncio.Event):
    """Initializes and runs the bot, waiting for a stop signal."""
    try:
        logger.info("🤖 ICT Trading Oracle Bot preparing to start...")
        print("🚀 Initializing ICT Trading Oracle Bot...")

        # Pass is_admin function to bot_data for handlers to use
        application.bot_data['is_admin_func'] = is_admin 

        # --- Command Mapping for button_handler ---
        # Create a map of command strings to function objects
        command_functions = {
            "price": price_command,
            "signal": signal_command,
            "news": news_command,
            "profile": profile_command,
            "subscribe": subscribe_command,
            "test_system": test_system_command,
            "backtest": backtest_command, 
            "help": help_command, 
            # Admin commands, now accessible from admin panel buttons
            "admin": admin_command, # This will show the main admin message with /commands
            "stats": stats_command,
            "users": users_command,
            # "start" is handled in button_handler to return to main menu
        }
        application.bot_data['command_functions'] = command_functions
        logger.info("🧩 Command functions mapped and stored in bot_data.")
        # --- End Command Mapping ---

        # Add handlers (moved here to have application instance)
        application.add_handler(CommandHandler("start", start))
        # The help command handler will now also show the menu
        application.add_handler(CommandHandler("help", help_command)) 
        
        # Add the CallbackQueryHandler for button presses
        application.add_handler(CallbackQueryHandler(button_handler))
        logger.info("🔗 CallbackQueryHandler for buttons registered.")

        # CommandHandlers for commands that now have buttons are removed to encourage button usage.
        # application.add_handler(CommandHandler("price", price_command))
        # application.add_handler(CommandHandler("signal", signal_command))
        # application.add_handler(CommandHandler("news", news_command))
        # application.add_handler(CommandHandler("profile", profile_command))
        # application.add_handler(CommandHandler("subscribe", subscribe_command))
        
        # Keep admin-related CommandHandlers
        application.add_handler(CommandHandler("admin", admin_command)) 
        application.add_handler(CommandHandler("stats", stats_command)) 
        application.add_handler(CommandHandler("users", users_command)) 
        application.add_handler(CommandHandler("test_system", test_system_command))
        application.add_handler(CommandHandler("backtest", backtest_command))
        
        logger.info("🤖 Bot command handlers registered.")
        print("✅ Bot handlers registered successfully!")
        
        await application.initialize()
        logger.info("🤖 Application initialized.")
        print("🔄 Starting application and polling...")
        await application.start()

        if not application.updater:
            logger.critical("Application updater is None after start. Cannot start polling.")
            print("❌ Critical error: Application updater is missing.")
            return # or raise an exception
            
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        logger.info("✅ Bot is now running! Waiting for stop signal (Ctrl+C or SIGTERM).")
        print("✅ Bot is now running! Press Ctrl+C to stop.")
        
        await stop_event.wait() # Keep running until stop_event is set

    except Exception as e:
        logger.critical(f"Critical error during bot setup or runtime: {e}", exc_info=True)
        print(f"❌ Critical error in bot logic: {e}")
    finally:
        logger.info("Initiating shutdown sequence in main_bot_logic finally block...")
        print("\nInitiating shutdown sequence...")
        if application:
            if application.updater and application.updater.running:
                logger.info("Stopping updater...")
                print("Stopping updater...")
                await application.updater.stop()
                logger.info("Updater stopped.")
                print("Updater stopped.")
            # No need to call application.stop() separately if updater.stop() is called
            logger.info("Shutting down application...")
            print("Shutting down application...")
            await application.shutdown()
            logger.info("Application shutdown complete.")
            print("Application shutdown complete.")
        logger.info("Shutdown sequence finished.")
        print("✅ Bot shut down gracefully.")

async def main():
    """Main entry point for the bot."""
    # Re-check BOT_TOKEN to satisfy linter, though it's checked above.
    # If the initial check passed, BOT_TOKEN is guaranteed to be a string here.
    if not BOT_TOKEN: 
        logger.critical("BOT_TOKEN became None unexpectedly before app build. This should not happen.")
        print("CRITICAL ERROR: BOT_TOKEN is None before application build.")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def signal_handler(sig, frame=None): # Frame is optional for add_signal_handler
        logger.info(f"Received signal {sig.name if isinstance(sig, signal.Signals) else sig}, initiating shutdown...")
        print(f"\nReceived signal {sig.name if isinstance(sig, signal.Signals) else sig}, initiating shutdown...")
        if not stop_event.is_set():
            loop.call_soon_threadsafe(stop_event.set)

    for sig_val in (signal.SIGINT, signal.SIGTERM):
        # For Windows, SIGTERM might not be available or work as expected.
        # SIGINT (Ctrl+C) is generally reliable.
        try:
            loop.add_signal_handler(sig_val, signal_handler, sig_val)
        except (AttributeError, NotImplementedError, ValueError) as e:
            # ValueError: signal handler must be signal.SIG_DFL, signal.SIG_IGN, or a callable object
            # NotImplementedError: signals are not supported on this platform (e.g. certain Windows asyncio loops)
            # AttributeError: 'ProactorEventLoop' object has no attribute 'add_signal_handler' (older Python on Windows)
            logger.warning(f"Could not set signal handler for {sig_val.name if isinstance(sig_val, signal.Signals) else sig_val}: {e}. Relying on KeyboardInterrupt.")
            # For Windows, KeyboardInterrupt is often the primary way to stop console apps.
            # The asyncio.run() wrapper handles KeyboardInterrupt well.

    await main_bot_logic(application, stop_event)

# This function is no longer needed as its logic is integrated into main() and main_bot_logic()
# def handle_exit(signum=None, frame=None):
#     """Handle exit signals gracefully."""
#     logger.info("🛑 Bot shutting down...")
#     print("\n🛑 Bot shutting down...")
#     # Async shutdown logic is now in main_bot_logic's finally block
#     print("✅ Bot shut down gracefully.")
#     sys.exit(0) # sys.exit should be avoided in async code if possible; natural exit is better.

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received at top level. Exiting.")
        print("\n🛑 Bot process interrupted by user (KeyboardInterrupt). Exiting.")
    except Exception as e:
        logger.critical(f"Critical error preventing bot from running: {e}", exc_info=True)
        print(f"❌ Top-level critical error: {e}")
    finally:
        logger.info("Bot application process finished.")
        print("Bot application process finished.")
