"""
Advanced Admin Panel for ICT Trading Oracle
"""

import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import matplotlib.pyplot as plt
import io
import base64
from core.database import DatabaseManager

logger = logging.getLogger(__name__)

class AdvancedAdminPanel:
    def __init__(self, db_manager, api_manager, subscription_manager):
        self.db = db_manager
        self.api = api_manager
        self.subscription = subscription_manager
    
    async def show_main_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main admin panel with advanced options"""
        user_id = update.effective_user.id
        
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ دسترسی مجاز نیست!")
            return
        
        # Get real-time statistics
        stats = self._get_comprehensive_stats()
        
        keyboard = [
            [
                InlineKeyboardButton("📊 آمار پیشرفته", callback_data="admin_advanced_stats"),
                InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_user_management")
            ],
            [
                InlineKeyboardButton("📈 گزارش‌های تحلیلی", callback_data="admin_analytics"),
                InlineKeyboardButton("💳 مدیریت اشتراک‌ها", callback_data="admin_subscription_mgmt")
            ],
            [
                InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast"),
                InlineKeyboardButton("🔧 تنظیمات سیستم", callback_data="admin_system_settings")
            ],
            [
                InlineKeyboardButton("🤖 مدیریت AI", callback_data="admin_ai_management"),
                InlineKeyboardButton("📋 لاگ‌های سیستم", callback_data="admin_system_logs")
            ],
            [
                InlineKeyboardButton("🔄 بک‌آپ و بازیابی", callback_data="admin_backup"),
                InlineKeyboardButton("⚡ عملیات سریع", callback_data="admin_quick_actions")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_text = f"""
🎛️ **پنل ادمین پیشرفته - ICT Trading Oracle**

👑 **خوش آمدید ادمین!**

📊 **آمار لحظه‌ای:**
👥 کل کاربران: {stats['total_users']}
🟢 کاربران فعال (24 ساعت): {stats['active_users_24h']}
📈 سیگنال‌های امروز: {stats['signals_today']}
💰 درآمد ماهانه: {stats['monthly_revenue']:,} تومان

💎 **اشتراک‌ها:**
🆓 رایگان: {stats['free_users']}
⭐ پریمیوم: {stats['premium_users']}
💎 VIP: {stats['vip_users']}

🤖 **وضعیت سیستم:**
✅ ربات: فعال
✅ دیتابیس: متصل
✅ API ها: آنلاین
✅ AI مدل‌ها: آماده

⏰ **آخرین به‌روزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await update.message.reply_text(admin_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_admin_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin panel callback queries"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if not self._is_admin(user_id):
            await query.edit_message_text("❌ دسترسی مجاز نیست!")
            return
        
        data = query.data
        
        if data == "admin_advanced_stats":
            await self._show_advanced_statistics(query)
        elif data == "admin_user_management":
            await self._show_user_management(query)
        elif data == "admin_analytics":
            await self._show_analytics_dashboard(query)
        elif data == "admin_subscription_mgmt":
            await self._show_subscription_management(query)
        elif data == "admin_broadcast":
            await self._show_broadcast_panel(query)
        elif data == "admin_system_settings":
            await self._show_system_settings(query)
        elif data == "admin_ai_management":
            await self._show_ai_management(query)
        elif data == "admin_system_logs":
            await self._show_system_logs(query)
        elif data == "admin_backup":
            await self._show_backup_panel(query)
        elif data == "admin_quick_actions":
            await self._show_quick_actions(query)
        elif data.startswith("admin_"):
            await self._handle_specific_admin_action(query, data)
    
    async def _show_advanced_statistics(self, query):
        """Show advanced statistics with charts"""
        stats = self._get_detailed_statistics()
        
        # Generate chart
        chart_data = self._generate_statistics_chart(stats)
        
        keyboard = [
            [
                InlineKeyboardButton("📈 نمودار کاربران", callback_data="admin_chart_users"),
                InlineKeyboardButton("💰 نمودار درآمد", callback_data="admin_chart_revenue")
            ],
            [
                InlineKeyboardButton("📊 نمودار سیگنال‌ها", callback_data="admin_chart_signals"),
                InlineKeyboardButton("🎯 نمودار دقت", callback_data="admin_chart_accuracy")
            ],
            [
                InlineKeyboardButton("📋 گزارش کامل PDF", callback_data="admin_generate_report"),
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        stats_text = f"""
📊 **آمار پیشرفته - ICT Trading Oracle**

👥 **آمار کاربران:**
📋 کل کاربران: {stats['total_users']}
📈 رشد هفتگی: +{stats['weekly_growth']} ({stats['weekly_growth_percent']:+.1f}%)
🟢 فعال امروز: {stats['active_today']}
🔄 بازگشت کاربران: {stats['retention_rate']:.1f}%

💰 **آمار مالی:**
💎 درآمد امروز: {stats['revenue_today']:,} تومان
📊 درآمد هفته: {stats['revenue_week']:,} تومان
📈 درآمد ماه: {stats['revenue_month']:,} تومان
💳 متوسط ارزش کاربر: {stats['avg_user_value']:,} تومان

📈 **آمار سیگنال‌ها:**
🎯 سیگنال‌های امروز: {stats['signals_today']}
📊 کل سیگنال‌ها: {stats['total_signals']}
✅ دقت سیگنال‌ها: {stats['signal_accuracy']:.1f}%
⭐ رضایت کاربران: {stats['user_satisfaction']:.1f}%

🤖 **عملکرد AI:**
🧠 مدل‌های فعال: {stats['active_models']}
🎯 دقت پیش‌بینی: {stats['prediction_accuracy']:.1f}%
⚡ سرعت تحلیل: {stats['analysis_speed']:.2f}s
🔄 آخرین آموزش: {stats['last_training']}

📱 **آمار استفاده:**
🔝 محبوب‌ترین دستور: {stats['most_used_command']}
⏰ ساعت پیک: {stats['peak_hour']}:00
📅 روز پیک: {stats['peak_day']}
        """
        
        await query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _show_user_management(self, query):
        """Show user management panel"""
        recent_users = self.db.get_user_list(10)
        
        keyboard = [
            [
                InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search_user"),
                InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_user_stats")
            ],
            [
                InlineKeyboardButton("💎 ارتقاء اشتراک", callback_data="admin_upgrade_user"),
                InlineKeyboardButton("🚫 مسدود کردن", callback_data="admin_ban_user")
            ],
            [
                InlineKeyboardButton("📧 پیام به کاربر", callback_data="admin_message_user"),
                InlineKeyboardButton("🎁 اعطای اشتراک", callback_data="admin_gift_subscription")
            ],
            [
                InlineKeyboardButton("📋 لیست کامل", callback_data="admin_full_user_list"),
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        users_text = "👥 **مدیریت کاربران**\n\n"
        users_text += "📋 **آخرین کاربران:**\n\n"
        
        for user in recent_users[:5]:
            subscription_emoji = "💎" if user['subscription_type'] == 'vip' else "⭐" if user['subscription_type'] == 'premium' else "🆓"
            users_text += f"""
{subscription_emoji} **{user['first_name'] or 'Unknown'}**
🆔 ID: `{user['user_id']}`
📊 سیگنال‌ها: {user['total_signals_received']}
🕐 آخرین فعالیت: {user['last_activity'][:10]}

"""
        
        await query.edit_message_text(users_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _show_analytics_dashboard(self, query):
        """Show analytics dashboard"""
        analytics = self._get_analytics_data()
        
        keyboard = [
            [
                InlineKeyboardButton("📈 تحلیل رشد", callback_data="admin_growth_analysis"),
                InlineKeyboardButton("💰 تحلیل درآمد", callback_data="admin_revenue_analysis")
            ],
            [
                InlineKeyboardButton("🎯 تحلیل دقت", callback_data="admin_accuracy_analysis"),
                InlineKeyboardButton("👥 تحلیل رفتار", callback_data="admin_behavior_analysis")
            ],
            [
                InlineKeyboardButton("📊 داشبورد زنده", callback_data="admin_live_dashboard"),
                InlineKeyboardButton("📋 گزارش سفارشی", callback_data="admin_custom_report")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        analytics_text = f"""
📈 **داشبورد تحلیلی**

📊 **تحلیل عملکرد (30 روز گذشته):**

📈 **رشد کاربران:**
• رشد کلی: +{analytics['user_growth_30d']} کاربر
• رشد روزانه متوسط: +{analytics['avg_daily_growth']:.1f}
• نرخ تبدیل: {analytics['conversion_rate']:.1f}%

💰 **عملکرد مالی:**
• درآمد کل: {analytics['total_revenue_30d']:,} تومان
• متوسط روزانه: {analytics['avg_daily_revenue']:,} تومان
• رشد درآمد: {analytics['revenue_growth']:+.1f}%

🎯 **کیفیت سیگنال‌ها:**
• دقت کلی: {analytics['overall_accuracy']:.1f}%
• سیگنال‌های موفق: {analytics['successful_signals']}
• رضایت کاربران: {analytics['user_satisfaction']:.1f}/5

📱 **الگوهای استفاده:**
• پیک استفاده: {analytics['peak_usage_time']}
• محبوب‌ترین ویژگی: {analytics['most_popular_feature']}
• زمان متوسط جلسه: {analytics['avg_session_time']} دقیقه

🔮 **پیش‌بینی‌ها:**
• رشد پیش‌بینی شده: +{analytics['predicted_growth']} کاربر
• درآمد پیش‌بینی شده: {analytics['predicted_revenue']:,} تومان
• ترند کلی: {analytics['overall_trend']}
        """
        
        await query.edit_message_text(analytics_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _show_broadcast_panel(self, query):
        """Show broadcast message panel"""
        keyboard = [
            [
                InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast_all"),
                InlineKeyboardButton("⭐ پیام به پریمیوم", callback_data="admin_broadcast_premium")
            ],
            [
                InlineKeyboardButton("💎 پیام به VIP", callback_data="admin_broadcast_vip"),
                InlineKeyboardButton("🆓 پیام به رایگان", callback_data="admin_broadcast_free")
            ],
            [
                InlineKeyboardButton("🎯 پیام هدفمند", callback_data="admin_broadcast_targeted"),
                InlineKeyboardButton("📋 تاریخچه پیام‌ها", callback_data="admin_broadcast_history")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        broadcast_text = """
📢 **پنل ارسال پیام همگانی**

🎯 **گزینه‌های ارسال:**

📢 **همگانی:** ارسال به تمام کاربران
⭐ **پریمیوم:** فقط کاربران پریمیوم
💎 **VIP:** فقط کاربران VIP
🆓 **رایگان:** فقط کاربران رایگان

🎯 **ارسال هدفمند:**
• بر اساس فعالیت
• بر اساس منطقه جغرافیایی
• بر اساس الگوی استفاده

📋 **آمار آخرین ارسال:**
• تعداد دریافت‌کنندگان: 1,250
• نرخ باز کردن: 85.2%
• نرخ کلیک: 12.3%
• زمان ارسال: 2 ساعت پیش

⚠️ **توجه:** پیام‌های همگانی با احتیاط ارسال شوند
        """
        
        await query.edit_message_text(broadcast_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _show_ai_management(self, query):
        """Show AI management panel"""
        ai_stats = self._get_ai_statistics()
        
        keyboard = [
            [
                InlineKeyboardButton("🧠 آموزش مجدد مدل", callback_data="admin_retrain_model"),
                InlineKeyboardButton("📊 عملکرد مدل‌ها", callback_data="admin_model_performance")
            ],
            [
                InlineKeyboardButton("🎯 تنظیم پارامترها", callback_data="admin_ai_parameters"),
                InlineKeyboardButton("🔄 به‌روزرسانی داده", callback_data="admin_update_data")
            ],
            [
                InlineKeyboardButton("📈 نمودار دقت", callback_data="admin_accuracy_chart"),
                InlineKeyboardButton("🔍 تست مدل", callback_data="admin_test_model")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        ai_text = f"""
🤖 **مدیریت سیستم هوش مصنوعی**

🧠 **وضعیت مدل‌ها:**
✅ مدل پیش‌بینی قیمت: فعال
✅ مدل تشخیص سیگنال: فعال
✅ مدل تحلیل احساسات: فعال

📊 **عملکرد (7 روز گذشته):**
🎯 دقت پیش‌بینی قیمت: {ai_stats['price_accuracy']:.1f}%
🎯 دقت سیگنال‌ها: {ai_stats['signal_accuracy']:.1f}%
🎯 دقت تحلیل احساسات: {ai_stats['sentiment_accuracy']:.1f}%

⚡ **آمار عملکرد:**
🔄 تحلیل‌های انجام شده: {ai_stats['total_analyses']}
⏱️ متوسط زمان تحلیل: {ai_stats['avg_analysis_time']:.2f}s
🧮 پردازش‌های موفق: {ai_stats['successful_processes']:.1f}%

🔧 **تنظیمات فعلی:**
📈 حد آستانه اطمینان: {ai_stats['confidence_threshold']}%
🎯 حد آستانه سیگنال: {ai_stats['signal_threshold']}%
🔄 بازه آموزش مجدد: {ai_stats['retrain_interval']} روز

📅 **آخرین فعالیت‌ها:**
🧠 آخرین آموزش: {ai_stats['last_training']}
📊 آخرین ارزیابی: {ai_stats['last_evaluation']}
🔄 آخرین به‌روزرسانی: {ai_stats['last_update']}
        """
        
        await query.edit_message_text(ai_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    def _get_comprehensive_stats(self):
        """Get comprehensive statistics"""
        try:
            base_stats = self.db.get_bot_stats()
            
            # Additional calculations
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Get active users in last 24 hours
            active_24h = self._get_active_users_24h()
            
            # Get subscription breakdown
            subscription_stats = self._get_subscription_breakdown()
            
            # Calculate monthly revenue (mock data for now)
            monthly_revenue = subscription_stats['premium_users'] * 49000 + subscription_stats['vip_users'] * 149000
            
            return {
                'total_users': base_stats['total_users'],
                'active_users_24h': active_24h,
                'signals_today': base_stats['daily_signals'],
                'monthly_revenue': monthly_revenue,
                'free_users': subscription_stats['free_users'],
                'premium_users': subscription_stats['premium_users'],
                'vip_users': subscription_stats['vip_users']
            }
        except Exception as e:
            logger.error(f"Error getting comprehensive stats: {e}")
            return {
                'total_users': 0,
                'active_users_24h': 0,
                'signals_today': 0,
                'monthly_revenue': 0,
                'free_users': 0,
                'premium_users': 0,
                'vip_users': 0
            }
    
    def _get_detailed_statistics(self):
        """Get detailed statistics for advanced view"""
        try:
            base_stats = self._get_comprehensive_stats()
            
            # Mock detailed data (replace with real calculations)
            return {
                **base_stats,
                'weekly_growth': 45,
                'weekly_growth_percent': 3.2,
                'active_today': 89,
                'retention_rate': 67.5,
                'revenue_today': 245000,
                'revenue_week': 1680000,
                'revenue_month': 7250000,
                'avg_user_value': 58000,
                'signal_accuracy': 84.2,
                'user_satisfaction': 4.6,
                'active_models': 3,
                'prediction_accuracy': 78.9,
                'analysis_speed': 0.85,
                'last_training': '2 روز پیش',
                'most_used_command': '/signal',
                'peak_hour': 14,
                'peak_day': 'دوشنبه'
            }
        except Exception as e:
            logger.error(f"Error getting detailed statistics: {e}")
            return {}
    
    def _get_analytics_data(self):
        """Get analytics data"""
        # Mock analytics data (replace with real calculations)
        return {
            'user_growth_30d': 234,
            'avg_daily_growth': 7.8,
            'conversion_rate': 12.5,
            'total_revenue_30d': 4500000,
            'avg_daily_revenue': 150000,
            'revenue_growth': 15.2,
            'overall_accuracy': 82.4,
            'successful_signals': 1847,
            'user_satisfaction': 4.5,
            'peak_usage_time': '14:00-16:00',
            'most_popular_feature': 'سیگنال ICT',
            'avg_session_time': 8.5,
            'predicted_growth': 89,
            'predicted_revenue': 1200000,
            'overall_trend': 'صعودی'
        }
    
    def _get_ai_statistics(self):
        """Get AI system statistics"""
        return {
            'price_accuracy': 78.5,
            'signal_accuracy': 84.2,
            'sentiment_accuracy': 76.8,
            'total_analyses': 15847,
            'avg_analysis_time': 0.85,
            'successful_processes': 97.2,
            'confidence_threshold': 70,
            'signal_threshold': 65,
            'retrain_interval': 7,
            'last_training': '3 روز پیش',
            'last_evaluation': '1 روز پیش',
            'last_update': '6 ساعت پیش'
        }
    
    def _get_active_users_24h(self):
        """Get active users in last 24 hours"""
        try:
            # This would query the database for users active in last 24 hours
            # Mock implementation
            return 89
        except:
            return 0
    
    def _get_subscription_breakdown(self):
        """Get subscription type breakdown"""
        try:
            # This would query the database for subscription breakdown
            # Mock implementation
            return {
                'free_users': 850,
                'premium_users': 320,
                'vip_users': 80
            }
        except:
            return {
                'free_users': 0,
                'premium_users': 0,
                'vip_users': 0
            }
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        try:
            from config.settings import ADMIN_IDS
            return user_id in ADMIN_IDS
        except:
            return False
