from pyrogram import Client, filters
from utils import is_check_admin
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton


@Client.on_message(filters.command('manage') & filters.group)
async def members_management(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ <b>Admin Rights Required!</b>\n\n<blockquote>You must be a group administrator to use this command.</blockquote>")
    btn = [[
        InlineKeyboardButton('🔊 Unmute All', callback_data='unmute_all_members'),
        InlineKeyboardButton('✨ Unban All', callback_data='unban_all_members')
    ],[
        InlineKeyboardButton('👢 Kick Muted Users', callback_data='kick_muted_members'),
        InlineKeyboardButton('🧹 Kick Deleted Accounts', callback_data='kick_deleted_accounts_members')
    ]]
    await message.reply_text("⚙️ <b>Group Members Manager</b>\n\n<blockquote>Select an action below to manage or clean up members in this group:</blockquote>", reply_markup=InlineKeyboardMarkup(btn))
  
  
@Client.on_message(filters.command('ban') & filters.group)
async def ban_chat_user(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ <b>Admin Rights Required!</b>\n\n<blockquote>You must be a group administrator to use this command.</blockquote>")
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.username or message.reply_to_message.from_user.id
    else:
        try:
            user_id = message.text.split(" ", 1)[1]
        except IndexError:
            return await message.reply_text("⚠️ <b>Missing User Details!</b>\n\n<blockquote>Please reply to a user's message or provide their User ID or @username. Example: <code>/ban @username</code></blockquote>")
    try:
        user_id = int(user_id)
    except ValueError:
        pass
    try:
        user = (await client.get_chat_member(message.chat.id, user_id)).user
    except:
        return await message.reply_text("❌ <b>User Not Found!</b>\n\n<blockquote>Could not locate the specified user in this group chat.</blockquote>")
    try:
        await client.ban_chat_member(message.chat.id, user_id)
    except:
        return await message.reply_text("⚠️ <b>Permission Denied!</b>\n\n<blockquote>I do not have the required administrator privileges to ban users in this group.</blockquote>")
    await message.reply_text(f"✅ <b>User Banned Successfully!</b>\n\n<blockquote>🚫 {user.mention} has been banned from <b>{message.chat.title}</b>.</blockquote>")


@Client.on_message(filters.command('mute') & filters.group)
async def mute_chat_user(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ <b>Admin Rights Required!</b>\n\n<blockquote>You must be a group administrator to use this command.</blockquote>")
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.username or message.reply_to_message.from_user.id
    else:
        try:
            user_id = message.text.split(" ", 1)[1]
        except IndexError:
            return await message.reply_text("⚠️ <b>Missing User Details!</b>\n\n<blockquote>Please reply to a user's message or provide their User ID or @username. Example: <code>/mute @username</code></blockquote>")
    try:
        user_id = int(user_id)
    except ValueError:
        pass
    try:
        user = (await client.get_chat_member(message.chat.id, user_id)).user
    except:
        return await message.reply_text("❌ <b>User Not Found!</b>\n\n<blockquote>Could not locate the specified user in this group chat.</blockquote>")
    try:
        await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions())
    except:
        return await message.reply_text("⚠️ <b>Permission Denied!</b>\n\n<blockquote>I do not have the required administrator privileges to mute users in this group.</blockquote>")
    await message.reply_text(f"✅ <b>User Muted Successfully!</b>\n\n<blockquote>🔇 {user.mention} has been muted in <b>{message.chat.title}</b>.</blockquote>")


@Client.on_message(filters.command(["unban", "unmute"]) & filters.group)
async def unban_chat_user(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ <b>Admin Rights Required!</b>\n\n<blockquote>You must be a group administrator to use this command.</blockquote>")
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.username or message.reply_to_message.from_user.id
    else:
        try:
            user_id = message.text.split(" ", 1)[1]
        except IndexError:
            return await message.reply_text("⚠️ <b>Missing User Details!</b>\n\n<blockquote>Please reply to a user's message or provide their User ID or @username. Example: <code>/unban @username</code></blockquote>")
    try:
        user_id = int(user_id)
    except ValueError:
        pass
    try:
        user = (await client.get_chat_member(message.chat.id, user_id)).user
    except:
        return await message.reply_text("❌ <b>User Not Found!</b>\n\n<blockquote>Could not locate the specified user in this group chat.</blockquote>")
    try:
        await client.unban_chat_member(message.chat.id, user_id)
    except:
        return await message.reply_text(f"⚠️ <b>Permission Denied!</b>\n\n<blockquote>I do not have the required administrator privileges to {message.command[0]} users in this group.</blockquote>")
    await message.reply_text(f"✅ <b>Action Completed!</b>\n\n<blockquote>✨ Successfully {message.command[0]}ed {user.mention} in <b>{message.chat.title}</b>.</blockquote>")
