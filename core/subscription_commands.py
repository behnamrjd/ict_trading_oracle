"""
Subscription Commands for ICT Trading Oracle
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import logging

logger = logging.getLogger(__name__)

class SubscriptionCommands:
    def __init__(self, db_manager, payment_manager, subscription_manager):
        self.db = db_manager
        self.payment = payment_manager
        self.subscription = subscription_manager
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show subscription plans"""
        user_id = update.effective_user.id
        
        # Log activity
        self.db.log_user_activity(user_id, '/subscribe')
        
        user_data = self.db.get_user(user_id)
        current_plan = user_data['subscription_type'] if user_data else 'free'
        
        keyboard = [
            [
                InlineKeyboardButton("💎 VIP - 149,000 تومان", callback_data="subscribe_vip"),
                InlineKeyboardButton("⭐ Premium - 49,000 تومان", callback_data="subscribe_premium")
            ],
            [
                InlineKeyboardButton("ℹ️ مقایسه پلن‌ها", callback_data="compare_plans"),
                InlineKeyboardButton("❓ راهنمای پرداخت", callback_data="payment_help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        subscribe_text = f"""
💳 **اشتراک ICT Trading Oracle**

📊 **پلن فعلی شما:** {current_plan.upper()}

🎯 **پلن‌های موجود:**

⭐ **Premium - 49,000 تومان/ماه**
• 50 سیگنال روزانه
• تحلیل‌های پیشرفته
• پشتیبانی ایمیل

💎 **VIP - 149,000 تومان/ماه**
• سیگنال‌های نامحدود
• تحلیل‌های اختصاصی
• پشتیبانی اولویت‌دار
• هشدارهای سفارشی

💡 **روش پرداخت:** ZarinPal (کارت‌های ایرانی)
🔒 **امنیت:** پرداخت کاملاً امن
        """
        
        await update.message.reply_text(subscribe_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_subscription_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle subscription callback buttons"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "subscribe_premium":
            await self._process_subscription(query, user_id, "premium")
        elif data == "subscribe_vip":
            await self._process_subscription(query, user_id, "vip")
        elif data == "compare_plans":
            await self._show_plan_comparison(query)
        elif data == "payment_help":
            await self._show_payment_help(query)
    
    async def _process_subscription(self, query, user_id, plan_type):
        """Process subscription purchase"""
        plan = self.subscription.get_plan_info(plan_type)
        if not plan:
            await query.edit_message_text("❌ پلن انتخابی معتبر نیست!")
            return
        
        # Create invoice
        invoice = self.subscription.create_subscription_invoice(user_id, plan_type)
        if not invoice:
            await query.edit_message_text("❌ خطا در ایجاد فاکتور!")
            return
        
        # Create payment request
        payment_result = self.payment.create_payment_request(
            amount=plan['price'],
            description=invoice['description'],
            user_id=user_id,
            subscription_type=plan_type
        )
        
        if payment_result['success']:
            keyboard = [
                [InlineKeyboardButton("💳 پرداخت", url=payment_result['payment_url'])],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_plans")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            payment_text = f"""
💳 **فاکتور پرداخت**

📦 **پلن:** {plan['name']}
💰 **مبلغ:** {plan['price']:,} تومان
⏰ **مدت:** {plan['duration_days']} روز

🔗 **کد پیگیری:** `{payment_result['authority']}`

⚠️ **توجه:**
• پس از پرداخت، اشتراک شما فعال می‌شود
• در صورت مشکل، کد پیگیری را ذخیره کنید
• اعتبار لینک پرداخت: 15 دقیقه

💡 **برای پرداخت روی دکمه زیر کلیک کنید:**
            """
            
            await query.edit_message_text(payment_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await query.edit_message_text(f"❌ خطا در ایجاد درخواست پرداخت:\n{payment_result['error']}")
    
    async def _show_plan_comparison(self, query):
        """Show plan comparison"""
        comparison_text = """
📊 **مقایسه پلن‌های اشتراک**

🆓 **رایگان:**
• 3 سیگنال روزانه
• تحلیل‌های پایه
• پشتیبانی عمومی

⭐ **Premium - 49,000 تومان:**
• 50 سیگنال روزانه
• تحلیل‌های پیشرفته
• پشتیبانی ایمیل
• دسترسی به اخبار اختصاصی

💎 **VIP - 149,000 تومان:**
• سیگنال‌های نامحدود
• تحلیل‌های اختصاصی
• پشتیبانی اولویت‌دار
• هشدارهای سفارشی
• گزارش‌های تخصصی
• مشاوره شخصی

💡 **توصیه:** برای تریدرهای حرفه‌ای VIP، برای مبتدیان Premium
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_plans")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(comparison_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _show_payment_help(self, query):
        """Show payment help"""
        help_text = """
❓ **راهنمای پرداخت**

💳 **روش‌های پرداخت:**
• کارت‌های بانکی ایرانی
• اینترنت بانک
• موبایل بانک

🔒 **امنیت:**
• پرداخت از طریق ZarinPal
• رمزگذاری SSL
• عدم ذخیره اطلاعات کارت

⚡ **فرآیند پرداخت:**
1. انتخاب پلن
2. کلیک روی "پرداخت"
3. وارد کردن اطلاعات کارت
4. تأیید پرداخت
5. فعالسازی خودکار اشتراک

📞 **پشتیبانی:**
در صورت مشکل با ادمین تماس بگیرید
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_plans")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)

    async def payment_success_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle successful payment (called by webhook or manual)"""
        # This would be called by your payment webhook
        # For now, we'll create a manual command for testing
        
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ دسترسی مجاز نیست!")
            return
        
        # Manual subscription activation for testing
        if context.args and len(context.args) >= 2:
            target_user_id = int(context.args[0])
            plan_type = context.args[1]
            
            success = self.subscription.activate_subscription(target_user_id, plan_type)
            
            if success:
                await update.message.reply_text(f"✅ اشتراک {plan_type} برای کاربر {target_user_id} فعال شد!")
                
                # Send notification to user
                try:
                    plan = self.subscription.get_plan_info(plan_type)
                    notification_text = f"""
🎉 **اشتراک شما فعال شد!**

📦 **پلن:** {plan['name']}
⏰ **مدت:** {plan['duration_days']} روز
🎯 **سیگنال‌های روزانه:** {'نامحدود' if plan['daily_signals'] == -1 else plan['daily_signals']}

💡 **از این لحظه می‌توانید از تمام امکانات استفاده کنید!**
                    """
                    
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=notification_text,
                        parse_mode='Markdown'
                    )
                except:
                    pass
            else:
                await update.message.reply_text("❌ خطا در فعالسازی اشتراک!")
        else:
            await update.message.reply_text("❌ فرمت: /activate_subscription <user_id> <plan_type>")
