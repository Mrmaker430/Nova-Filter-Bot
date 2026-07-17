import re
import time
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from info import ADMINS, INDEX_EXTENSIONS
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp, get_readable_time

lock = asyncio.Lock()

@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    _, ident, chat, lst_msg_id, skip = query.data.split("#")
    if ident == 'yes':
        msg = query.message
        await msg.edit("🚀 <b>Starting Indexing Process...</b>")
        try:
            chat = int(chat)
        except:
            chat = chat
        await index_files_to_db(int(lst_msg_id), chat, msg, bot, int(skip))
    elif ident == 'cancel':
        temp.CANCEL = True
        await query.message.edit("🛑 <b>Cancelling Indexing Process...</b>")


@Client.on_message(filters.command('index') & filters.private & filters.user(ADMINS))
async def send_for_index(bot, message):
    if lock.locked():
        return await message.reply('⏳ <b>Indexing in Progress!</b>\n\n<blockquote>Please wait until the current indexing task finishes before starting a new one.</blockquote>')
    i = await message.reply("📨 <b>Send Last Message or Link</b>\n\n<blockquote>Please forward the last message from the channel or paste its message link to set the indexing boundary:</blockquote>")
    msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    if not msg:
        await i.delete()
        return await message.reply('⏱️ <b>Request Timed Out!</b>\n\n<blockquote>You took too long to respond. Please start `/index` again when ready.</blockquote>')
    await i.delete()
    if msg.text and msg.text.startswith("https://t.me"):
        try:
            msg_link = msg.text.split("/")
            last_msg_id = int(msg_link[-1])
            chat_id = msg_link[-2]
            if chat_id.isnumeric():
                chat_id = int(("-100" + chat_id))
        except:
            await message.reply('❌ <b>Invalid Message Link!</b>\n\n<blockquote>Please make sure you send a valid Telegram public/private message link.</blockquote>')
            return
    elif msg.forward_origin and msg.forward_origin.type == enums.MessageOriginType.CHANNEL:
        last_msg_id = msg.forward_origin.message_id 
        chat_id = msg.forward_origin.chat.username or msg.forward_origin.chat.id
    else:
        await message.reply('⚠️ <b>Invalid Input!</b>\n\n<blockquote>Please forward a message directly from the channel or send a valid message link.</blockquote>')
        return
    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f'❌ <b>Error Occurred!</b>\n\n<blockquote>⚠️ Details: <code>{e}</code></blockquote>')

    if chat.type != enums.ChatType.CHANNEL:
        return await message.reply("⚠️ <b>Channels Only!</b>\n\n<blockquote>I can only index files from channels where I am added as an administrator.</blockquote>")

    s = await message.reply("⏩ <b>Enter Skip Message ID</b>\n\n<blockquote>Please enter the message ID number from where you want to start indexing (or send <code>0</code> to start from the beginning):</blockquote>")
    msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    if not msg:
        await s.delete()
        return await message.reply('⏱️ <b>Request Timed Out!</b>\n\n<blockquote>You took too long to respond. Please start `/index` again when ready.</blockquote>')
    await s.delete()
    try:
        skip = int(msg.text)
    except:
        return await message.reply("❌ <b>Invalid Number!</b>\n\n<blockquote>Please send a valid integer number (e.g. <code>0</code> or <code>100</code>).</blockquote>")

    buttons = [[
        InlineKeyboardButton('✅ Yes, Index', callback_data=f'index#yes#{chat_id}#{last_msg_id}#{skip}')
    ],[
        InlineKeyboardButton('✖️ Close', callback_data='close_data'),
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply(f'🗳️ <b>Confirm Channel Indexing</b>\n\n<blockquote>📢 <b>Channel:</b> {chat.title}\n📊 <b>Total Messages:</b> <code>{last_msg_id}</code></blockquote>\n\nDo you want to proceed with indexing this channel?', reply_markup=reply_markup)


async def index_files_to_db(lst_msg_id, chat, msg, bot, skip):
    start_time = time.time()
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    badfiles = 0
    current = skip
    
    async with lock:
        try:
            async for message in bot.iter_messages(chat, lst_msg_id, skip):
                time_taken = get_readable_time(time.time()-start_time)
                if temp.CANCEL:
                    temp.CANCEL = False
                    await msg.edit(f"🛑 <b>Successfully Cancelled!</b>\n\n<blockquote>⏱️ <b>Time Taken:</b> {time_taken}\n✅ <b>Saved to Database:</b> <code>{total_files}</code> files\n⏩ <b>Duplicate Files Skipped:</b> <code>{duplicate}</code>\n🗑️ <b>Deleted Messages Skipped:</b> <code>{deleted}</code>\n💬 <b>Non-Media Skipped:</b> <code>{no_media + unsupported}</code>\n📂 <b>Unsupported Media:</b> <code>{unsupported}</code>\n❌ <b>Errors Occurred:</b> <code>{errors}</code>\n⚠️ <b>Bad Files Ignored:</b> <code>{badfiles}</code></blockquote>")
                    return
                current += 1
                if current % 30 == 0:
                    btn = [[
                        InlineKeyboardButton('⚠️ Cancel', callback_data=f'index#cancel#{chat}#{lst_msg_id}#{skip}')
                    ]]
                    try:
                        await msg.edit_text(text=f"🔄 <b>Indexing Progress:</b>\n\n<blockquote>📬 <b>Messages Received:</b> <code>{current}</code>\n✅ <b>Saved to Database:</b> <code>{total_files}</code>\n⏩ <b>Duplicate Skipped:</b> <code>{duplicate}</code>\n🗑️ <b>Deleted Skipped:</b> <code>{deleted}</code>\n💬 <b>Non-Media Skipped:</b> <code>{no_media + unsupported}</code>\n📂 <b>Unsupported Media:</b> <code>{unsupported}</code>\n❌ <b>Errors Occurred:</b> <code>{errors}</code>\n⚠️ <b>Bad Files Ignored:</b> <code>{badfiles}</code></blockquote>", reply_markup=InlineKeyboardMarkup(btn))
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                if message.empty:
                    deleted += 1
                    continue
                elif not message.media:
                    no_media += 1
                    continue
                elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue
                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue
                elif not (str(media.file_name).lower()).endswith(tuple(INDEX_EXTENSIONS)):
                    unsupported += 1
                    continue
                media.caption = message.caption
                file_name = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.file_name))
                sts = await save_file(media)
                if sts == 'suc':
                    total_files += 1
                elif sts == 'dup':
                    duplicate += 1
                elif sts == 'err':
                    errors += 1
        except Exception as e:
            await msg.reply(f"❌ <b>Index Canceled Due to Error!</b>\n\n<blockquote>⚠️ Details: <code>{e}</code></blockquote>")
        else:
            time_taken = get_readable_time(time.time()-start_time)
            await msg.edit(f"🎉 <b>Successfully Saved <code>{total_files}</code> Files to Database!</b>\n\n<blockquote>⏱️ <b>Time Taken:</b> {time_taken}\n⏩ <b>Duplicate Files Skipped:</b> <code>{duplicate}</code>\n🗑️ <b>Deleted Messages Skipped:</b> <code>{deleted}</code>\n💬 <b>Non-Media Skipped:</b> <code>{no_media + unsupported}</code>\n📂 <b>Unsupported Media:</b> <code>{unsupported}</code>\n❌ <b>Errors Occurred:</b> <code>{errors}</code>\n⚠️ <b>Bad Files Ignored:</b> <code>{badfiles}</code></blockquote>")
