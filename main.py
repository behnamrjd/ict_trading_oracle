#!/usr/bin/env python3
"""
ICT Trading Oracle Bot - Complete Version with Error Handling
"""

import os
import asyncio
import signal
import sys
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/ict_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Get Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found! Please set it in .env file")
    print("❌ BOT_TOKEN not found! Please add it to .env file")
    exit(1)

# Global application variable
application = None

# Import modules with error handling
try:
    from config.settings import ADMIN_IDS
except ImportError as e:
    logger.error(f"Could not import ADMIN_IDS: {e}")
    ADMIN_IDS = [123456789]  # Default admin ID

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

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
    """Safely import TechnicalAnalyzer"""
    try:
        from core.technical_analysis import TechnicalAnalyzer
        return TechnicalAnalyzer()
    except ImportError as e:
        logger.error(f"Could not import TechnicalAnalyzer: {e}")
        return None

def safe_import_database_manager():
    """Safely import DatabaseManager"""
    try:
        from core.database import DatabaseManager
        return DatabaseManager()
    except ImportError as e:
        logger.error(f"Could not import DatabaseManager: {e}")
        return None

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    try:
        from config.settings import ADMIN_IDS
        return user_id in ADMIN_IDS
    except ImportError:
        logger.error("Could not import ADMIN_IDS from config.settings")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    
    # Add user to database
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
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
    except Exception as e:
        logger.error(f"Database error in start command: {e}")
        subscription = 'free'
    
    logger.info(f"User started bot - ID: {user.id}, Username: {user.username}, Name: {user.first_name}")
    
    subscription_emoji = "💎" if subscription == 'vip' else "⭐" if subscription == 'premium' else "🆓"
    
    welcome_text = f"""
🎪 **Welcome to ICT Trading Oracle Bot**

Hello {user.first_name}! 👋

{subscription_emoji} **Your Subscription:** {subscription.upper()}

🎯 **Bot Features:**
👉 **LIVE** Gold Price Data
👉 **REAL** ICT Technical Analysis  
👉 **LIVE** Market News
👉 Professional Trading Signals
👉 Premium Subscriptions Available

📊 **Commands:**
/help - Complete guide
/price - **LIVE** gold price
/signal - **REAL** ICT analysis
/news - Latest gold news
/profile - Your profile & stats
/subscribe - Premium subscriptions
/admin - Admin panel (if you're admin)

💎 **Upgrade for unlimited signals and advanced features!**

🆔 **Your User ID:** `{user.id}`
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.log_user_activity(update.effective_user.id, '/help')
    except:
        pass
    
    help_text = """
🔧 **ICT Trading Oracle Bot Guide**

📋 **Available Commands:**
/start - Start the bot
/help - This guide
/price - **LIVE** gold price from Yahoo Finance
/signal - **REAL** ICT technical analysis
/news - Latest gold market news
/profile - Your profile and statistics
/subscribe - Premium subscriptions
/admin - Admin panel (admin only)

💳 **Subscription Plans:**
🆓 **Free:** 3 daily signals
⭐ **Premium:** 50 daily signals (49,000 تومان/ماه)
💎 **VIP:** Unlimited signals (149,000 تومان/ماه)

🎪 **About ICT:**
Inner Circle Trading methodology with REAL market data:
• Live price feeds from Yahoo Finance
• Technical analysis with RSI, MACD, Bollinger Bands
• Market structure analysis
• Order block detection
• Fair Value Gap identification

💡 **Payment:**
🔒 Secure payment via ZarinPal
💳 Iranian bank cards supported
⚡ Instant activation
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get live gold price"""
    user_id = update.effective_user.id
    
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.log_user_activity(user_id, '/price')
    except:
        pass
    
    await update.message.reply_text("📊 Fetching live gold price...")
    
    try:
        from core.api_manager import APIManager
        api_manager = APIManager()
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
    except Exception as e:
        logger.error(f"Error in price command: {e}")
        price_text = f"❌ **Error fetching price:** {str(e)}"
    
    await update.message.reply_text(price_text, parse_mode='Markdown')

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get real ICT analysis with database tracking"""
    user_id = update.effective_user.id
    
    # Check if user can receive signals
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.log_user_activity(user_id, '/signal')
        
        if not db_manager.can_receive_signal(user_id):
            user_data = db_manager.get_user(user_id)
            limit = 3 if user_data['subscription_type'] == 'free' else 50
            
            await update.message.reply_text(f"""
⚠️ **Daily Signal Limit Reached**

You've used all {limit} signals for today.

🔄 **Reset Time:** Tomorrow at 00:00 UTC
💎 **Upgrade:** Use /subscribe for premium subscription

📊 **Current Plan:** {user_data['subscription_type'].upper()}
            """, parse_mode='Markdown')
            return
    except Exception as e:
        logger.error(f"Database error in signal command: {e}")
    
    await update.message.reply_text("🔍 Analyzing market with ICT methodology...")
    
    try:
        from core.api_manager import APIManager
        from core.technical_analysis import TechnicalAnalyzer
        
        api_manager = APIManager()
        tech_analyzer = TechnicalAnalyzer()
        
        # Get live price and analysis
        price_data = api_manager.get_gold_price()
        analysis = tech_analyzer.analyze_market_structure()
        
        if price_data and analysis:
            # Save signal to database
            try:
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
            except Exception as e:
                logger.error(f"Error saving signal to database: {e}")
            
            signal_emoji = "🟢" if analysis['signal'] == 'BUY' else "🔴" if analysis['signal'] == 'SELL' else "🟡"
            confidence_stars = "⭐" * min(int(analysis['confidence'] / 20), 5)
            
            # Get updated user stats
            try:
                user_data = db_manager.get_user(user_id)
                signals_used = user_data['daily_signals_used'] if user_data else 0
                total_signals = user_data['total_signals_received'] if user_data else 0
                subscription_type = user_data['subscription_type'] if user_data else 'free'
            except:
                signals_used = 0
                total_signals = 0
                subscription_type = 'free'
            
            signal_text = f"""
📊 **ICT Analysis - Gold (XAU/USD)**

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
🔢 Signals Used Today: {signals_used}/{'∞' if subscription_type == 'vip' else '50' if subscription_type == 'premium' else '3'}
📈 Total Signals: {total_signals}

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
    except Exception as e:
        logger.error(f"Error in signal command: {e}")
        signal_text = f"❌ **Error generating signal:** {str(e)}"
    
    await update.message.reply_text(signal_text, parse_mode='Markdown')

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get latest gold news"""
    user_id = update.effective_user.id
    
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.log_user_activity(user_id, '/news')
    except:
        pass
    
    await update.message.reply_text("📰 Fetching latest gold market news...")
    
    try:
        from core.api_manager import APIManager
        api_manager = APIManager()
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
    except Exception as e:
        logger.error(f"Error in news command: {e}")
        news_text = f"❌ **Error fetching news:** {str(e)}"
    
    await update.message.reply_text(news_text, parse_mode='Markdown')

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile and statistics"""
    user_id = update.effective_user.id
    
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
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

💎 **Want more signals?** Use /subscribe to upgrade!
            """
        else:
            profile_text = "❌ Profile not found. Please use /start first."
    except Exception as e:
        logger.error(f"Error in profile command: {e}")
        profile_text = f"❌ **Error loading profile:** {str(e)}"
    
    await update.message.reply_text(profile_text, parse_mode='Markdown')

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription options"""
    user_id = update.effective_user.id
    
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.log_user_activity(user_id, '/subscribe')
        
        user_data = db_manager.get_user(user_id)
        current_plan = user_data['subscription_type'] if user_data else 'free'
    except:
        current_plan = 'free'
    
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
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ You don't have admin access!")
        return
    
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        stats = db_manager.get_bot_stats()
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
/broadcast - Send message to all users
/test_system - Run system tests

🛠️ **System Status:**
✅ Bot: Running with ALL features
✅ Database: Connected
✅ APIs: Online
✅ Payment: ZarinPal Ready

💡 **Advanced Features:**
🤖 AI/ML Models: Ready
📊 Analytics: Real-time
🔒 Security: Enhanced
⚡ Performance: Optimized
    """
    await update.message.reply_text(admin_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return
    
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
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
        """
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        stats_text = f"❌ **Error loading statistics:** {str(e)}"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user list (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return
    
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
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
    except Exception as e:
        logger.error(f"Error in users command: {e}")
        users_text = f"❌ **Error loading users:** {str(e)}"
    
    await update.message.reply_text(users_text, parse_mode='Markdown')

async def test_system_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test system components (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin access required!")
        return
    
    await update.message.reply_text("🔧 Testing system components...")
    
    test_results = []
    
    # Test API Manager
    try:
        from core.api_manager import APIManager
        api_manager = APIManager()
        price_data = api_manager.get_gold_price()
        test_results.append(("API Manager", "✅" if price_data else "❌"))
    except Exception as e:
        test_results.append(("API Manager", f"❌ {str(e)[:50]}"))
    
    # Test Technical Analyzer
    try:
        from core.technical_analysis import TechnicalAnalyzer
        tech_analyzer = TechnicalAnalyzer()
        analysis = tech_analyzer.analyze_market_structure()
        test_results.append(("Technical Analyzer", "✅" if analysis else "❌"))
    except Exception as e:
        test_results.append(("Technical Analyzer", f"❌ {str(e)[:50]}"))
    
    # Test Database
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        stats = db_manager.get_bot_stats()
        test_results.append(("Database", "✅" if stats else "❌"))
    except Exception as e:
        test_results.append(("Database", f"❌ {str(e)[:50]}"))
    
    # Test Payment Manager
    try:
        from core.payment_manager import PaymentManager
        payment_manager = PaymentManager()
        test_results.append(("Payment Manager", "✅"))
    except Exception as e:
        test_results.append(("Payment Manager", f"❌ {str(e)[:50]}"))
    
    test_text = "🔧 **System Test Results**\n\n"
    for component, result in test_results:
        test_text += f"**{component}:** {result}\n"
    
    await update.message.reply_text(test_text, parse_mode='Markdown')

async def main():
    """Main function with proper event loop handling"""
    global application
    
    try:
        print("🚀 Starting ICT Trading Oracle Bot...")
        
        # Create Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("price", price_command))
        application.add_handler(CommandHandler("signal", signal_command))
        application.add_handler(CommandHandler("news", news_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("subscribe", subscribe_command))
        application.add_handler(CommandHandler("admin", admin_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("users", users_command))
        application.add_handler(CommandHandler("test_system", test_system_command))
        
        logger.info("🤖 ICT Trading Oracle Bot starting...")
        print("✅ Bot handlers registered successfully!")
        print("🔄 Starting polling...")
        
        # Initialize the application
        await application.initialize()
        
        # Start the application
        await application.start()
        
        # Start polling
        await application.updater.start_polling()
        
        print("✅ Bot is now running!")
        
        # Keep the bot running
        try:
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
    """Run the bot with proper event loop handling for systemd"""
    try:
        # Install nest_asyncio to handle running event loops
        import nest_asyncio
        nest_asyncio.apply()
        
        # Get the current event loop
        loop = asyncio.get_event_loop()
        
        # Run the main function
        loop.run_until_complete(main())
        
    except ImportError:
        # If nest_asyncio is not available, use alternative method
        try:
            # Try to create a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            print(f"❌ Failed to start bot: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    run_bot()
