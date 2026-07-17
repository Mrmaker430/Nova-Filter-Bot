from pyrogram import Client, filters
import time
from database.users_chats_db import db
from info import ADMINS
from utils import broadcast_messages, groups_broadcast_messages, temp, get_readable_time
import asyncio
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

lock = asyncio.Lock()

@Client.on_callback_query(filters.regex(r'^broadcast_cancel'))
async def broadcast_cancel(bot, query):
    _, ident = query.data.split("#")
    if ident == 'users':
        await query.message.edit("🛑 <b>Cancelling Users Broadcast...</b>")
        temp.USERS_CANCEL = True
    elif ident == 'groups':
        temp.GROUPS_CANCEL = True
        await query.message.edit("🛑 <b>Cancelling Groups Broadcast...</b>")
               
@Client.on_message(filters.command(["broadcast", "pin_broadcast"]) & filters.user(ADMINS) & filters.reply)
async def users_broadcast(bot, message):
    if lock.locked():
        return await message.reply("⏳ <b>Broadcast in Progress!</b>\n\n<blockquote>Please wait until the current broadcast task finishes before starting a new one.</blockquote>")
    if message.command[0] == 'pin_broadcast':
        pin = True
    else:
        pin = False
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    b_sts = await message.reply_text(text="📢 <b>Broadcasting to All Users...</b>\n\n<blockquote>⏳ Sending message across the user database, please wait...</blockquote>")
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    failed = 0
    success = 0

    async with lock:
        for user in users:
            time_taken = get_readable_time(time.time()-start_time)
            if temp.USERS_CANCEL:
                temp.USERS_CANCEL = False
                await b_sts.edit(f"🛑 <b>Users Broadcast Cancelled!</b>\n\n<blockquote>⏱️ <b>Time Taken:</b> {time_taken}\n👥 <b>Total Users:</b> <code>{total_users}</code>\n📬 <b>Completed:</b> <code>{done} / {total_users}</code>\n✅ <b>Success:</b> <code>{success}</code></blockquote>")
                return
            sts = await broadcast_messages(int(user['id']), b_msg, pin)
            if sts == 'Success':
                success += 1
            elif sts == 'Error':
                failed += 1
            done += 1
            if not done % 20:
                btn = [[
                    InlineKeyboardButton('⚠️ Cancel', callback_data='broadcast_cancel#users')
                ]]
                await b_sts.edit(f"🔄 <b>Users Broadcast Progress:</b>\n\n<blockquote>👥 <b>Total Users:</b> <code>{total_users}</code>\n📬 <b>Completed:</b> <code>{done} / {total_users}</code>\n✅ <b>Success:</b> <code>{success}</code></blockquote>", reply_markup=InlineKeyboardMarkup(btn))
        await b_sts.edit(f"🎉 <b>Users Broadcast Completed!</b>\n\n<blockquote>⏱️ <b>Time Taken:</b> {time_taken}\n👥 <b>Total Users:</b> <code>{total_users}</code>\n📬 <b>Completed:</b> <code>{done} / {total_users}</code>\n✅ <b>Success:</b> <code>{success}</code></blockquote>")


@Client.on_message(filters.command(["grp_broadcast", "pin_grp_broadcast"]) & filters.user(ADMINS) & filters.reply)
async def groups_broadcast(bot, message):
    if lock.locked():
        return await message.reply("⏳ <b>Broadcast in Progress!</b>\n\n<blockquote>Please wait until the current broadcast task finishes before starting a new one.</blockquote>")
    if message.command[0] == 'pin_grp_broadcast':
        pin = True
    else:
        pin = False
    chats = await db.get_all_chats()
    b_msg = message.reply_to_message
    b_sts = await message.reply_text(text="📢 <b>Broadcasting to All Groups...</b>\n\n<blockquote>⏳ Sending message across all connected group chats, please wait...</blockquote>")
    start_time = time.time()
    total_chats = await db.total_chat_count()
    done = 0
    failed = 0
    success = 0

    async with lock:
        for chat in chats:
            time_taken = get_readable_time(time.time()-start_time)
            if temp.GROUPS_CANCEL:
                temp.GROUPS_CANCEL = False
                await b_sts.edit(f"🛑 <b>Groups Broadcast Cancelled!</b>\n\n<blockquote>⏱️ <b>Time Taken:</b> {time_taken}\n👥 <b>Total Groups:</b> <code>{total_chats}</code>\n📬 <b>Completed:</b> <code>{done} / {total_chats}</code>\n✅ <b>Success:</b> <code>{success}</code>\n❌ <b>Failed:</b> <code>{failed}</code></blockquote>")
                return
            sts = await groups_broadcast_messages(int(chat['id']), b_msg, pin)
            if sts == 'Success':
                success += 1
            elif sts == 'Error':
                failed += 1
            done += 1
            if not done % 20:
                btn = [[
                    InlineKeyboardButton('⚠️ Cancel', callback_data='broadcast_cancel#groups')
                ]]
                await b_sts.edit(f"🔄 <b>Groups Broadcast Progress:</b>\n\n<blockquote>👥 <b>Total Groups:</b> <code>{total_chats}</code>\n📬 <b>Completed:</b> <code>{done} / {total_chats}</code>\n✅ <b>Success:</b> <code>{success}</code>\n❌ <b>Failed:</b> <code>{failed}</code></blockquote>", reply_markup=InlineKeyboardMarkup(btn))    
        await b_sts.edit(f"🎉 <b>Groups Broadcast Completed!</b>\n\n<blockquote>⏱️ <b>Time Taken:</b> {time_taken}\n👥 <b>Total Groups:</b> <code>{total_chats}</code>\n📬 <b>Completed:</b> <code>{done} / {total_chats}</code>\n✅ <b>Success:</b> <code>{success}</code>\n❌ <b>Failed:</b> <code>{failed}</code></blockquote>")


