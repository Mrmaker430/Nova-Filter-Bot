from info import ADMINS, LOG_CHANNEL
from speedtest import Speedtest, ConfigRetrievalError, SpeedtestBestServerFailure
from pyrogram import Client, filters, enums
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters
from utils import get_size
from datetime import datetime
import os
import html
import yt_dlp, httpx


def format_download_duration(seconds):
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


async def log_download_copy(client, downloaded_file, thumbnail_file, message, link, title, duration):
    user = message.from_user
    full_name = html.escape(" ".join(filter(None, [user.first_name, user.last_name])) or "Unknown")
    safe_title = html.escape(title or "Video")
    safe_link = html.escape(link)
    caption = (
        "#Download\n"
        f"<b>Name:</b> {full_name}\n"
        f"<b>User ID:</b> <code>{user.id}</code>\n"
        f"<b>Link:</b> {safe_link}\n"
        f"<b>Title:</b> {safe_title}\n"
        f"<b>Duration:</b> <code>{format_download_duration(duration)}</code>"
    )
    try:
        await client.send_video(
            chat_id=LOG_CHANNEL,
            video=downloaded_file,
            caption=caption,
            duration=duration,
            thumb=thumbnail_file,
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        try:
            await client.send_message(
                chat_id=LOG_CHANNEL,
                text=caption,
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:
            pass

@Client.on_message(filters.command('id'))
async def showid(client, message):
    chat_type = message.chat.type
    replied_to_msg = bool(message.reply_to_message)
    if replied_to_msg:
        return await message.reply_text(f"ℹ️ <b>Forwarded Channel Info:</b>\n\n<blockquote>📢 <b>Channel Name:</b> {replied_to_msg.chat.title}\n🆔 <b>Channel ID:</b> <code>{replied_to_msg.chat.id}</code></blockquote>")
    if chat_type == enums.ChatType.PRIVATE:
        await message.reply_text(f'★ User ID: <code>{message.from_user.id}</code>')

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await message.reply_text(f'★ Group ID: <code>{message.chat.id}</code>')

    elif chat_type == enums.ChatType.CHANNEL:
        await message.reply_text(f'★ Channel ID: <code>{message.chat.id}</code>')


@Client.on_message(filters.command('speedtest') & filters.user(ADMINS))
async def speedtest(client, message):
    #from - https://github.com/weebzone/WZML-X/blob/master/bot/modules/speedtest.py
    msg = await message.reply_text("⚡ <b>Initiating Speedtest...</b>\n\n<blockquote>⏳ Testing server latency, download speed, and upload speed...</blockquote>")
    try:
        speed = Speedtest()
        speed.get_best_server()
    except (ConfigRetrievalError, SpeedtestBestServerFailure):
        await msg.edit("❌ <b>Speedtest Failed!</b>\n\n<blockquote>Cannot connect to speedtest server right now. Please try again later.</blockquote>")
        return
    speed.download()
    speed.upload()
    speed.results.share()
    result = speed.results.dict()
    photo = result['share']
    text = f'''
➲ <b>SPEEDTEST INFO</b>
┠ <b>Upload:</b> <code>{get_size(result['upload'])}/s</code>
┠ <b>Download:</b>  <code>{get_size(result['download'])}/s</code>
┠ <b>Ping:</b> <code>{result['ping']} ms</code>
┠ <b>Time:</b> <code>{datetime.strptime(result['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")}</code>
┠ <b>Data Sent:</b> <code>{get_size(int(result['bytes_sent']))}</code>
┖ <b>Data Received:</b> <code>{get_size(int(result['bytes_received']))}</code>

➲ <b>SPEEDTEST SERVER</b>
┠ <b>Name:</b> <code>{result['server']['name']}</code>
┠ <b>Country:</b> <code>{result['server']['country']}, {result['server']['cc']}</code>
┠ <b>Sponsor:</b> <code>{result['server']['sponsor']}</code>
┠ <b>Latency:</b> <code>{result['server']['latency']}</code>
┠ <b>Latitude:</b> <code>{result['server']['lat']}</code>
┖ <b>Longitude:</b> <code>{result['server']['lon']}</code>

➲ <b>CLIENT DETAILS</b>
┠ <b>IP Address:</b> <code>{result['client']['ip']}</code>
┠ <b>Latitude:</b> <code>{result['client']['lat']}</code>
┠ <b>Longitude:</b> <code>{result['client']['lon']}</code>
┠ <b>Country:</b> <code>{result['client']['country']}</code>
┠ <b>ISP:</b> <code>{result['client']['isp']}</code>
┖ <b>ISP Rating:</b> <code>{result['client']['isprating']}</code>
'''
    await message.reply_photo(photo=photo, caption=text)
    await msg.delete()


@Client.on_message(filters.command("info"))
async def who_is(client, message):
    status_message = await message.reply_text(
        "🔍 <b>Fetching User Info...</b>\n\n<blockquote>⏳ Retrieving account details and statistics...</blockquote>"
    )
    if message.reply_to_message:
        from_user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        from_user_id = message.command[1]
    else:
        from_user_id = message.from_user.id
    try:
        from_user = await client.get_users(from_user_id)
    except Exception as error:
        await status_message.edit(f"❌ <b>Error Fetching Info:</b>\n\n<blockquote><code>{error}</code></blockquote>")
        return

    message_out_str = ""
    message_out_str += f"<b>➲First Name:</b> {from_user.first_name}\n"
    last_name = from_user.last_name or 'Not have'
    message_out_str += f"<b>➲Last Name:</b> {last_name}\n"
    message_out_str += f"<b>➲Telegram ID:</b> <code>{from_user.id}</code>\n"
    username = f'@{from_user.username}' if from_user.username else 'Not have'
    dc_id = from_user.dc_id or "Not found"
    message_out_str += f"<b>➲Data Centre:</b> <code>{dc_id}</code>\n"
    message_out_str += f"<b>➲Username:</b> {username}\n"
    message_out_str += f"<b>➲Last Online:</b> {last_online(from_user)}\n"
    message_out_str += f"<b>➲User 𝖫𝗂𝗇𝗄:</b> <a href='tg://user?id={from_user.id}'><b>Click Here</b></a>\n"
    if message.chat.type in [enums.ChatType.SUPERGROUP, enums.ChatType.GROUP]:
        try:
            chat_member_p = await message.chat.get_member(from_user.id)
            joined_date = chat_member_p.joined_date.strftime('%Y.%m.%d %H:%M:%S') if chat_member_p.joined_date else 'Not found'
            message_out_str += (
                "<b>➲Joined this Chat on:</b> <code>"
                f"{joined_date}"
                "</code>\n"
            )
        except UserNotParticipant:
            pass
    chat_photo = from_user.photo
    if chat_photo:
        local_user_photo = await client.download_media(
            message=chat_photo.big_file_id
        )
        await message.reply_photo(
            photo=local_user_photo,
            reply_parameters=ReplyParameters(message_id=message.id),
            caption=message_out_str,
            parse_mode=enums.ParseMode.HTML,
            disable_notification=True
        )
        os.remove(local_user_photo)
    else:
        await message.reply_text(
            text=message_out_str,
            reply_parameters=ReplyParameters(message_id=message.id),
            parse_mode=enums.ParseMode.HTML,
            disable_notification=True
        )
    await status_message.delete()



def last_online(from_user):
    time = ""
    if from_user.is_bot:
        time += "🤖 Bot :("
    elif from_user.status == enums.UserStatus.RECENTLY:
        time += "Recently"
    elif from_user.status == enums.UserStatus.LAST_WEEK:
        time += "Within the last week"
    elif from_user.status == enums.UserStatus.LAST_MONTH:
        time += "Within the last month"
    elif from_user.status == enums.UserStatus.LONG_AGO:
        time += "A long time ago :("
    elif from_user.status == enums.UserStatus.ONLINE:
        time += "Currently Online"
    elif from_user.status == enums.UserStatus.OFFLINE:
        time += from_user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S")
    return time


@Client.on_message(filters.command('download'))
async def download_video(client, message):
    if len(message.command) > 1:
        link = message.command[1]
    else:
        return await message.reply("⚠️ <b>Missing Video Link!</b>\n\n<blockquote><b>Usage:</b> <code>/download https://youtube.com/watch?v=...</code></blockquote>")

    status_msg = await message.reply("⏳ Downloading video, please wait...")

    user_id = message.from_user.id
    downloaded_file = None
    thumbnail_file = None

    try:
        os.makedirs("yt_dlp_downloads", exist_ok=True)

        ydl_opts = {
            'outtmpl': f'yt_dlp_downloads/{user_id}_%(title)s.%(ext)s',
            'format': 'best',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            title = info.get('title', 'Video')
            duration = info.get('duration', 0)
            thumbnail_url = info.get('thumbnail', None)
            downloaded_file = ydl.prepare_filename(info)

        if thumbnail_url:
            thumbnail_file = f"yt_dlp_downloads/{user_id}_thumb.jpg"
            async with httpx.AsyncClient() as http:
                response = await http.get(thumbnail_url)
                with open(thumbnail_file, 'wb') as f:
                    f.write(response.content)

        await status_msg.edit("📤 Uploading to Telegram...")

        await client.send_video(
            chat_id=message.chat.id,
            video=downloaded_file,
            caption=f"🎬 **{title}**",
            duration=duration,
            thumb=thumbnail_file,
            reply_parameters=ReplyParameters(message_id=message.id),
        )
        await log_download_copy(client, downloaded_file, thumbnail_file, message, link, title, duration)

        await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        await status_msg.edit(f"❌ <b>Download Failed!</b>\n\n<blockquote><code>{str(e)}</code></blockquote>")

    except Exception as e:
        await status_msg.edit(f"❌ <b>An Error Occurred!</b>\n\n<blockquote><code>{str(e)}</code></blockquote>")

    finally:
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        if thumbnail_file and os.path.exists(thumbnail_file):
            os.remove(thumbnail_file)
            