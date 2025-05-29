# Keyboards and Menus 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📈 دریافت قیمت", callback_data="price"),
            InlineKeyboardButton("🔔 دریافت سیگنال", callback_data="signal"),
        ],
        [
            InlineKeyboardButton("📰 مشاهده اخبار", callback_data="news"),
            InlineKeyboardButton("👤 پروفایل کاربری", callback_data="profile"),
        ],
        [
            InlineKeyboardButton("💳 اشتراک", callback_data="subscribe"),
            InlineKeyboardButton("⚙️ تست سیستم", callback_data="test_system"),
        ],
        [
            InlineKeyboardButton("📊 بک تست", callback_data="backtest"),
            InlineKeyboardButton("❓ راهنما", callback_data="help"),
        ],
        [
            InlineKeyboardButton("👑 پنل ادمین", callback_data="admin_panel"),
        ],
        # Admin commands can be added here conditionally later
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📊 آمار ربات", callback_data="stats"),
            InlineKeyboardButton("👥 مدیریت کاربران", callback_data="users"),
        ],
        [
            InlineKeyboardButton("⚙️ تست سیستم", callback_data="test_system"),
            InlineKeyboardButton("📈 بک تست", callback_data="backtest"),
        ],
        [
            InlineKeyboardButton("⬅️ بازگشت به منوی اصلی", callback_data="start"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Placeholder for a function to decide which menu to show
# async def get_relevant_keyboard(user_id):
#     # Logic to check if user is admin
#     # if is_admin(user_id):
#     #     return get_admin_menu_keyboard()
#     return get_main_menu_keyboard()
