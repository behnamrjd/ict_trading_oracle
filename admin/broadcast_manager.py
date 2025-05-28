"""
Broadcast Manager for ICT Trading Oracle
"""

import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

class BroadcastManager:
    def __init__(self, bot_token, db_manager):
        self.bot = Bot(token=bot_token)
        self.db = db_manager
    
    async def broadcast_message(self, message_text, target_group="all", image_url=None):
        """Broadcast message to specified user group"""
        try:
            # Get target users
            if target_group == "all":
                users = self.db.get_all_users()
            elif target_group == "premium":
                users = self.db.get_users_by_subscription("premium")
            elif target_group == "vip":
                users = self.db.get_users_by_subscription("vip")
            elif target_group == "free":
                users = self.db.get_users_by_subscription("free")
            else:
                users = []
            
            if not users:
                return {
                    'success': False,
                    'message': 'No users found for the specified group'
                }
            
            # Send messages
            successful_sends = 0
            failed_sends = 0
            
            for user in users:
                try:
                    if image_url:
                        await self.bot.send_photo(
                            chat_id=user['user_id'],
                            photo=image_url,
                            caption=message_text,
                            parse_mode='Markdown'
                        )
                    else:
                        await self.bot.send_message(
                            chat_id=user['user_id'],
                            text=message_text,
                            parse_mode='Markdown'
                        )
                    
                    successful_sends += 1
                    
                    # Add small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                    
                except TelegramError as e:
                    failed_sends += 1
                    logger.warning(f"Failed to send message to user {user['user_id']}: {e}")
                    
                    # If user blocked the bot, mark as inactive
                    if "blocked" in str(e).lower():
                        self.db.mark_user_inactive(user['user_id'])
            
            # Log broadcast
            self._log_broadcast(message_text, target_group, successful_sends, failed_sends)
            
            return {
                'success': True,
                'total_users': len(users),
                'successful_sends': successful_sends,
                'failed_sends': failed_sends,
                'success_rate': (successful_sends / len(users)) * 100 if users else 0
            }
            
        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def _log_broadcast(self, message, target_group, successful, failed):
        """Log broadcast activity"""
        try:
            # This would log to database
            logger.info(f"Broadcast sent - Target: {target_group}, Success: {successful}, Failed: {failed}")
        except Exception as e:
            logger.error(f"Error logging broadcast: {e}")
