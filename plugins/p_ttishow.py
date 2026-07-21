import random
import os
import sys
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from pyrogram.errors import MessageTooLong, PeerIdInvalid
from info import ADMINS, LOG_CHANNEL, PICS, SUPPORT_LINK, UPDATES_LINK, REQUEST_FORCE_SUB_CHANNEL
from database.users_chats_db import db
from utils import temp, get_settings, safe_format
from Script import script


@Client.on_chat_member_updated()
async def welcome(bot, message):
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return
    
    if message.new_chat_member and not message.old_chat_member:
        if message.new_chat_member.user.id == temp.ME:
            buttons = [[
                InlineKeyboardButton('📢 Updates', url=UPDATES_LINK),
                InlineKeyboardButton('💬 Support', url=SUPPORT_LINK)
            ]]
            reply_markup=InlineKeyboardMarkup(buttons)
            user = message.from_user.mention if message.from_user else "Dear"
            await bot.send_photo(chat_id=message.chat.id, photo=random.choice(PICS), caption=f"👋 <b>Hello {user},</b>\n\n<blockquote>✨ Thank you for adding me to <b>{message.chat.title}</b>!</blockquote>\n\n🛡️ Don't forget to promote me as <b>Admin</b> with full permissions to enable all auto-filtering features! For questions or help, join our support group below 👇", reply_markup=reply_markup)
            if not await db.get_chat(message.chat.id):
                total = await bot.get_chat_members_count(message.chat.id)
                username = f'@{message.chat.username}' if message.chat.username else 'Private'
                await bot.send_message(LOG_CHANNEL, script.NEW_GROUP_TXT.format(message.chat.title, message.chat.id, username, total))       
                await db.add_chat(message.chat.id, message.chat.title)
            return
        settings = await get_settings(message.chat.id)
        if settings["welcome"]:
            WELCOME = settings['welcome_text']
            welcome_msg = safe_format(
                WELCOME,
                mention = message.new_chat_member.user.mention,
                title = message.chat.title
            )
            await bot.send_message(chat_id=message.chat.id, text=welcome_msg)


@Client.on_message(filters.command('restart') & filters.user(ADMINS))
async def restart_bot(bot, message):
    msg = await message.reply("🔄 <b>Restarting Bot & Reloading Modules...</b>")
    with open('restart.txt', 'w+') as file:
        file.write(f"{msg.chat.id}\n{msg.id}")
    os.execl(sys.executable, sys.executable, "bot.py")

@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_a_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('⚠️ <b>Missing Chat ID!</b>\n\n<blockquote>Please provide a valid numeric Chat ID along with the command. Example: <code>/ban_chat -100123456789</code></blockquote>')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason provided."
    try:
        chat = int(chat)
    except:
        chat = chat
    try:
        buttons = [[
            InlineKeyboardButton('💬 Support', url=SUPPORT_LINK)
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat,
            text=f'👋 <b>Goodbye!</b>\n\nMy administrator has instructed me to leave this group.\n<blockquote>📌 <b>Reason:</b> <code>{reason}</code></blockquote>\n\nIf you need to add me again or have any questions, please contact our support group below 👇',
            reply_markup=reply_markup,
        )
        await bot.leave_chat(chat)
        await message.reply(f"<b>✅️ Successfully bot left from this group - `{chat}`</b>")
    except Exception as e:
        await message.reply(f'❌ <b>Operation Failed!</b>\n\n<blockquote>⚠️ Error details: <code>{e}</code></blockquote>')

@Client.on_message(filters.command('ban_grp') & filters.user(ADMINS))
async def disable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('⚠️ <b>Missing Chat ID!</b>\n\n<blockquote>Please provide a valid numeric Chat ID along with the command. Example: <code>/ban_chat -100123456789</code></blockquote>')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason provided."
    try:
        chat_ = int(chat)
    except:
        return await message.reply('❌ <b>Invalid Chat ID!</b>\n\n<blockquote>Please enter a valid numeric Telegram Chat ID starting with <code>-100</code>.</blockquote>')
    cha_t = await db.get_chat(int(chat_))
    if not cha_t:
        return await message.reply("⚠️ <b>Chat Not Found!</b>\n\n<blockquote>🥲 This chat ID is not currently registered in our database. Make sure the bot is added as an administrator to the group!</blockquote>")
    if cha_t['is_disabled']:
        return await message.reply(f"ℹ️ <b>Chat Already Disabled!</b>\n\n<blockquote>Reason: <code>{cha_t['reason']}</code></blockquote>")
    await db.disable_chat(int(chat_), reason)
    temp.BANNED_CHATS.append(int(chat_))
    await message.reply('✅ <b>Chat Successfully Disabled!</b>\n\n<blockquote>This group has been deactivated from auto-filtering.</blockquote>')
    try:
        buttons = [[
            InlineKeyboardButton('💬 Support', url=SUPPORT_LINK)
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat_, 
            text=f'👋 <b>Notice!</b>\n\nThis chat has been disabled by my administrator and I am leaving.\n<blockquote>📌 <b>Reason:</b> <code>{reason}</code></blockquote>\n\nIf you believe this is a mistake, please contact our support group below 👇',
            reply_markup=reply_markup)
        await bot.leave_chat(chat_)
    except Exception as e:
        await message.reply(f"❌ <b>Operation Failed!</b>\n\n<blockquote>⚠️ Error details: <code>{e}</code></blockquote>")

@Client.on_message(filters.command('unban_grp') & filters.user(ADMINS))
async def re_enable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('⚠️ <b>Missing Chat ID!</b>\n\n<blockquote>Please provide a valid numeric Chat ID along with the command. Example: <code>/ban_chat -100123456789</code></blockquote>')
    chat = message.command[1]
    try:
        chat_ = int(chat)
    except:
        return await message.reply('❌ <b>Invalid Chat ID!</b>\n\n<blockquote>Please enter a valid numeric Telegram Chat ID starting with <code>-100</code>.</blockquote>')
    sts = await db.get_chat(int(chat))
    if not sts:
        return await message.reply("⚠️ <b>Chat Not Found!</b>\n\n<blockquote>🥲 This chat ID is not currently registered in our database. Make sure the bot is added as an administrator to the group!</blockquote>")
    if not sts.get('is_disabled'):
        return await message.reply('ℹ️ <b>Chat Currently Active!</b>\n\n<blockquote>This group is already active and has not been disabled.</blockquote>')
    await db.re_enable_chat(int(chat_))
    temp.BANNED_CHATS.remove(int(chat_))
    await message.reply("✅ <b>Chat Re-Enabled!</b>\n\n<blockquote>This group is now active again and auto-filter is functioning normally.</blockquote>")

@Client.on_message(filters.command('invite_link') & filters.user(ADMINS))
async def gen_invite_link(bot, message):
    if len(message.command) == 1:
        return await message.reply('⚠️ <b>Missing Chat ID!</b>\n\n<blockquote>Please provide a valid numeric Chat ID along with the command. Example: <code>/ban_chat -100123456789</code></blockquote>')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        return await message.reply('❌ <b>Invalid Chat ID!</b>\n\n<blockquote>Please enter a valid numeric Telegram Chat ID starting with <code>-100</code>.</blockquote>')
    try:
        link = await bot.create_chat_invite_link(chat)
    except Exception as e:
        return await message.reply(f'❌ <b>Operation Failed!</b>\n\n<blockquote>⚠️ Error details: <code>{e}</code></blockquote>')
    await message.reply(f'🔗 <b>Invite Link Generated:</b>\n\n<blockquote>{link.invite_link}</blockquote>')

@Client.on_message(filters.command('ban_user') & filters.user(ADMINS))
async def ban_a_user(bot, message):
    if len(message.command) == 1:
        return await message.reply('⚠️ <b>Missing User Details!</b>\n\n<blockquote>Please provide a User ID or @Username after the command. Example: <code>/ban_user @username</code></blockquote>')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason provided."
    try:
        chat = int(chat)
    except:
        pass
    try:
        k = await bot.get_users(chat)
    except Exception as e:
        return await message.reply(f'❌ <b>Operation Failed!</b>\n\n<blockquote>⚠️ Error details: <code>{e}</code></blockquote>')
    else:
        if k.id in ADMINS:
            return await message.reply('🚫 <b>Action Not Allowed!</b>\n\n<blockquote>You cannot ban an administrator!</blockquote>')
        jar = await db.get_ban_status(k.id)
        if jar['is_banned']:
            return await message.reply(f"⚠️ <b>User Already Banned!</b>\n\n<blockquote>User {k.mention} is already restricted.\nReason: <code>{jar['ban_reason']}</code></blockquote>")
        await db.ban_user(k.id, reason)
        temp.BANNED_USERS.append(k.id)
        await message.reply(f"✅ <b>User Banned Successfully!</b>\n\n<blockquote>🚫 {k.mention} has been restricted from using the bot.</blockquote>")
   
@Client.on_message(filters.command('unban_user'))
async def unban_a_user(bot, message):
    if message.from_user.id not in ADMINS:
        return
    if len(message.command) == 1:
        return await message.reply('⚠️ <b>Missing User Details!</b>\n\n<blockquote>Please provide a User ID or @Username after the command. Example: <code>/ban_user @username</code></blockquote>')
    r = message.text.split(None)
    if len(r) > 1:
        reason = message.text.split(None, 1)[1]
    else:
        reason = "No reason Provided"
    try:
        chat = int(reason)
    except:
        chat = reason
    try:
        k = await bot.get_users(chat)
    except PeerIdInvalid:
        return await message.reply("❌ <b>Operation Failed!</b>\n\n<blockquote>⚠️ Error details: <code>PeerIdInvalid</code></blockquote>")
    except Exception as e:
        return await message.reply(f'❌ <b>Operation Failed!</b>\n\n<blockquote>⚠️ Error details: <code>{e}</code></blockquote>')
    else:
        jar = await db.get_ban_status(k.id)
        if not jar['is_banned']:
            return await message.reply(f"ℹ️ <b>User Not Banned!</b>\n\n<blockquote>User {k.mention} is currently active and has no ban restrictions.</blockquote>")
        await db.remove_ban(k.id)
        if k.id in temp.BANNED_USERS:
            temp.BANNED_USERS.remove(k.id)
        await message.reply(f"✅ <b>User Unbanned Successfully!</b>\n\n<blockquote>✨ {k.mention} can now use the bot and all its services normally.</blockquote>")
    
@Client.on_message(filters.command('users') & filters.user(ADMINS))
async def list_users(bot, message):
    raju = await message.reply('🔄 <b>Fetching Users List...</b>\n\n<blockquote>⏳ Retrieving database records, please wait...</blockquote>')
    users = await db.get_all_users()
    out = "Users saved in database are:\n\n"
    for user in users:
        out += f"**Name:** {user['name']}\n**ID:** `{user['id']}`"
        if user['ban_status']['is_banned']:
            out += ' (Banned User)'
        if user['verify_status']['is_verified']:
            out += ' (Verified User)'
        out += '\n\n'
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open('users.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('users.txt', caption="List of users")
        await raju.delete()
        os.remove('users.txt')

@Client.on_message(filters.command('chats') & filters.user(ADMINS))
async def list_chats(bot, message):
    raju = await message.reply('🔄 <b>Fetching Chats List...</b>\n\n<blockquote>⏳ Retrieving group chat records, please wait...</blockquote>')
    chats = await db.get_all_chats()
    out = "Chats saved in database are:\n\n"
    for chat in chats:
        out += f"**Title:** {chat['title']}\n**ID:** `{chat['id']}`"
        if chat['chat_status']['is_disabled']:
            out += ' (Disabled Chat)'
        out += '\n\n'
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open('chats.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('chats.txt', caption="List of chats")
        await raju.delete()
        os.remove('chats.txt')


@Client.on_chat_join_request()
async def join_reqs(client, message: ChatJoinRequest):
    if REQUEST_FORCE_SUB_CHANNEL and message.chat.id == int(REQUEST_FORCE_SUB_CHANNEL):
        if not db.find_join_req(message.from_user.id):
            await db.add_join_req(message.from_user.id)


@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    await db.del_join_req()
    await message.reply('🗑️ <b>Join Requests Cleared!</b>\n\n<blockquote>All pending join requests have been removed from the database.</blockquote>')
