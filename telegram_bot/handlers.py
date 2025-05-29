"""
Telegram Bot Handlers
"""

from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

def setup_handlers(application: Application):
    """Setup all bot handlers"""
    # This function is called from main.py but not used in current implementation
    # All handlers are already set up in main.py
    pass

# Import command functions from main.py - this might need adjustment based on project structure
# For example, if main.py has functions like: async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
# We might need to do: from main import price_command, signal_command # ... and so on
# Or, refactor command functions into a separate module.

# Placeholder for command functions that would ideally be imported or refactored
async def placeholder_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command_name: str):
    # This function simulates calling the actual command handlers from main.py
    # In a real scenario, you'd call the respective functions from main.py here.
    # e.g., if command_name == "price": await main_price_command(update, context)
    
    # For now, we'll just acknowledge the command via the callback query if possible
    query = update.callback_query
    if query:
        await query.edit_message_text(text=f"تابع دستور {command_name} فراخوانی شد (هنوز به main.py متصل نشده است).")
    elif update.message:
        await update.message.reply_text(text=f"تابع دستور {command_name} فراخوانی شد (هنوز به main.py متصل نشده است).")

# No direct imports from main.py needed if using context.bot_data for command map

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data:
        # logger.warning("CallbackQuery or query.data is None in button_handler.")
        if query: # Attempt to answer even if data is missing, to remove loading icon
            await query.answer(text="خطایی رخ داد، دوباره تلاش کنید.")
        return

    await query.answer()  # Answer the callback query successfully

    command_name = query.data
    # user_id = query.from_user.id if query.from_user else "UnknownUser"
    # chat_id = query.message.chat_id if query.message else "UnknownChat"

    # logger.info(f"User {user_id} in chat {chat_id} pressed button: {command_name}")

    command_functions = context.bot_data.get('command_functions', {})
    is_user_admin_func = context.bot_data.get('is_admin_func', lambda x: False)
    user_id = query.from_user.id if query.from_user else None

    if command_name == "admin_panel":
        if user_id and is_user_admin_func(user_id):
            from telegram_bot.keyboards import get_admin_menu_keyboard
            if query.message:
                await query.edit_message_text(
                    text="👑 **پنل مدیریت** 👑\n\nدستور مورد نظر را انتخاب کنید:", 
                    reply_markup=get_admin_menu_keyboard()
                )
            else: # Should not happen for a button press
                pass 
        else:
            await query.answer("شما اجازه دسترسی به این بخش را ندارید.", show_alert=True)
        return # Handled admin_panel, exit

    if command_name in command_functions:
        # Retrieve the actual command function from the map
        actual_command_function = command_functions[command_name]
        try:
            # Call the command function. 
            # Ensure the original command functions in main.py can handle being called with 
            # an update that has callback_query instead of message for some fields if they rely on it.
            # Or, they should primarily use update.effective_user and update.effective_chat if possible.
            await actual_command_function(update, context)
        except Exception as e:
            # logger.error(f"Error executing command '{command_name}' from button: {e}", exc_info=True)
            if query.message: # Check if we can edit the message
                try:
                    await query.edit_message_text(text=f"متاسفانه در اجرای دستور \'{command_name}\' مشکلی پیش آمد.")
                except Exception as edit_e:
                    # logger.error(f"Error editing message after command execution error: {edit_e}", exc_info=True)
                    pass # If editing fails, we can't do much more here
            # If there's no query.message, we can't easily send a message back in this context
            # without more information (like the original chat_id if stored separately).
    elif command_name == "help": # Special handling for help if it wasn't in command_functions or needs specific logic
        from telegram_bot.keyboards import get_main_menu_keyboard 
        if query.message:
            await query.edit_message_text(text="برای استفاده از ربات، از دکمه‌های زیر استفاده کنید:", reply_markup=get_main_menu_keyboard())
    elif command_name == "start": # Handle "Back to Main Menu" from admin panel
        from telegram_bot.keyboards import get_main_menu_keyboard
        if query.message:
            await query.edit_message_text(
                text="منوی اصلی ربات:",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        # logger.warning(f"Unknown command '{command_name}' received from button.")
        if query.message: # Check if we can edit the message
            await query.edit_message_text(text=f"دستور ناشناخته از طریق دکمه: {command_name}")

# The old setup_handlers function in this file is not used as handlers are set up in main.py.
# If it were to be used, it should register this button_handler with a CallbackQueryHandler.
# Example (if this file was responsible for setting up its own handlers):
# def setup_telegram_handlers(application: Application):
#     application.add_handler(CallbackQueryHandler(button_handler))
