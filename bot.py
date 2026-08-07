import logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logging.getLogger('pyrogram').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

import os
import time
import asyncio
try:
    import uvloop
    ul = True
except ImportError:
    ul = False
    pass

from pyrogram import types, Client, StopPropagation
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.errors import FloodWait
from aiohttp import web
from typing import Union, Optional, AsyncGenerator

from web import web_app
from info import URL, INDEX_CHANNELS, SUPPORT_GROUP, LOG_CHANNEL, API_ID, DATA_DATABASE_URL, API_HASH, BOT_TOKEN, PORT, BIN_CHANNEL, ADMINS, SECOND_FILES_DATABASE_URL, FILES_DATABASE_URL, FORCE_SUB_CHANNELS, REQUEST_FORCE_SUB_CHANNEL, AUTO_FILTER, PM_SEARCH
from utils import temp, get_readable_time, check_premium
from database.users_chats_db import db
from database.ia_filterdb import setup_database

if ul:
    uvloop.install()

class Bot(Client):
    def __init__(self):
        super().__init__(
            name='Auto_Filter_Bot',
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins={"root": "plugins"}
        )
        self.listeners = {}
        self.add_handler(MessageHandler(self._repair_mode_message_handler), group=-2)
        self.add_handler(CallbackQueryHandler(self._repair_mode_cb_handler), group=-2)
        self.add_handler(MessageHandler(self._listener_handler), group=-1)

    async def _repair_mode_message_handler(self, client: Client, message: types.Message):
        if await db.get_repair_mode():
            if message.from_user and message.from_user.id in ADMINS:
                return
            await message.reply("🛠️ <b>System Under Maintenance!</b>\n\n<blockquote>⚙️ Our bot is currently undergoing scheduled maintenance or repair mode. We will be back online shortly!</blockquote>")
            raise StopPropagation
            
    async def _repair_mode_cb_handler(self, client: Client, query: types.CallbackQuery):
        if await db.get_repair_mode():
            if query.from_user and query.from_user.id in ADMINS:
                return
            await query.answer("🛠️ System Under Maintenance! Our bot is currently undergoing scheduled repairs.", show_alert=True)
            raise StopPropagation

    async def _listener_handler(self, client: Client, message: types.Message):
        if not message.chat or not message.from_user:
            return
        
        listener_id = (message.chat.id, message.from_user.id)
        if listener_id in self.listeners:
            future = self.listeners[listener_id]
            if not future.done():
                future.set_result(message)
                raise StopPropagation

    async def listen(self, chat_id: int, user_id: int, timeout: int = 60) -> Optional[types.Message]:
        future = asyncio.get_event_loop().create_future()
        listener_id = (chat_id, user_id)
        
        if listener_id in self.listeners:
            old_future = self.listeners[listener_id]
            if not old_future.done():
                old_future.cancel()
                
        self.listeners[listener_id] = future
        
        try:
            message = await asyncio.wait_for(future, timeout)
            return message
        except asyncio.TimeoutError:
            return None
        finally:
            if self.listeners.get(listener_id) is future:
                self.listeners.pop(listener_id, None)

    async def start(self, **kwargs):
        logger.info('Setting up your database, please wait a moment...')
        await setup_database()
        logger.info('Successfully setup the database!, Now starting the bot...')
        await super().start()
        temp.START_TIME = time.time()
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats

        if os.path.exists('restart.txt'):
            with open("restart.txt") as file:
                chat_id, msg_id = map(int, file)
            try:
                await self.edit_message_text(chat_id=chat_id, message_id=msg_id, text="✅ <b>Bot Restarted Successfully!</b>\n\n<blockquote>🚀 All modules and plugins reloaded cleanly.</blockquote>")
            except:
                pass
            os.remove('restart.txt')

        temp.BOT = self
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        
        app = web.AppRunner(web_app)
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

        asyncio.create_task(check_premium(self))
        try:
            await self.send_message(chat_id=LOG_CHANNEL, text=f"<b>{me.mention} Restarted! 🤖</b>")
        except Exception as log_err:
            logger.error(f"Failed to send restart message to LOG_CHANNEL: {log_err}. Please ensure the bot is an administrator in the LOG_CHANNEL.")
        logger.info(f"Bot [@{me.username}] and webapp [{URL}] is started now ✓")

    async def stop(self, **kwargs):
        await super().stop()
        logger.info("Bot Stopped! Bye...")

    async def iter_messages(self: Client, chat_id: Union[int, str], limit: int, offset: int = 0) -> Optional[AsyncGenerator[types.Message, None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1

if __name__ == "__main__":
    app = Bot()
    app.run()