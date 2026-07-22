import asyncio
import re
import logging
from pyrogram import Client, filters, enums, StopPropagation
from utils import is_check_admin
from database.users_chats_db import db
from info import ADMINS

logger = logging.getLogger(__name__)

# Pattern to detect URLs
LINK_REGEX = re.compile(
    r'(https?://\S+|www\.\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(/\S*)?|t\.me/\S+)',
    re.IGNORECASE
)

@Client.on_message(filters.group & filters.incoming & ~filters.service, group=-3)
async def link_remover_handler(client, message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if the chat is connected and active
    chat_status = await db.get_chat(chat_id)
    if not chat_status:
        return
    if chat_status.get('is_disabled', False):
        return

    # Admins should be allowed to send links
    if user_id in ADMINS:
        return
    if await is_check_admin(client, chat_id, user_id):
        return

    # Check for link existence in entities or text/caption regex
    has_link = False

    # Check entities
    if message.entities:
        for entity in message.entities:
            if entity.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]:
                has_link = True
                break

    if not has_link and message.caption_entities:
        for entity in message.caption_entities:
            if entity.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]:
                has_link = True
                break

    # Regex search as fallback (e.g. raw text links not parsed by Telegram yet, or subdomains/links)
    if not has_link:
        text = message.text or message.caption or ""
        if LINK_REGEX.search(text):
            has_link = True

    if has_link:
        try:
            # Delete user's message first
            await message.delete()
        except Exception as e:
            logger.error(f"Failed to delete link message in chat {chat_id}: {e}")
            return

        try:
            # Send warning message using client.send_message
            warning_text = (
                f"⚠️ {message.from_user.mention}, <b>links are not allowed in this group!</b>\n"
                f"<blockquote>Your message was deleted automatically to protect the community.</blockquote>"
            )
            warning_msg = await client.send_message(chat_id, warning_text, parse_mode=enums.ParseMode.HTML)
            
            # Run background task to delete the warning message after 15 seconds
            async def delete_warning_after_delay(msg, delay=15):
                await asyncio.sleep(delay)
                try:
                    await msg.delete()
                except Exception:
                    pass

            asyncio.create_task(delete_warning_after_delay(warning_msg))
        except Exception as e:
            logger.error(f"Failed to send warning message in chat {chat_id}: {e}")

        # Stop propagation to other handler groups since the message has been deleted
        raise StopPropagation
