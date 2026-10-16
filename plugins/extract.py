import asyncio
import os
import re
import logging
import aiofiles
import tempfile
import uuid
import time
import requests

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegraph import Telegraph
from pymediainfo import MediaInfo

from database.ia_filterdb import get_file_details
from info import BIN_CHANNEL

try:
    from dreamxbotz.util.file_properties import get_name
except ImportError:
    def get_name(msg):
        if not msg:
            return "Media"
        media = getattr(msg, msg.media.value, None) if getattr(msg, "media", None) else None
        if media:
            return getattr(media, "file_name", None) or getattr(media, "title", None) or "Media"
        return getattr(msg, "file_name", None) or "Media"

logger = logging.getLogger(__name__)

# ==================== TELEGRAPH INIT ====================
TELEGRAPH_ACCESS_TOKEN = (
    os.environ.get("TELEGRAPH_ACCESS_TOKEN")
    or "38a8ac190ac77ad863fa0c3fa98bdf0bb563fa200211b168062e5313b401"
)

def _init_telegraph():
    """Try token first; validate it; fall back to anonymous account on failure."""
    if TELEGRAPH_ACCESS_TOKEN:
        try:
            t = Telegraph(access_token=TELEGRAPH_ACCESS_TOKEN)
            t.get_account_info()
            return t
        except Exception:
            logger.warning("Invalid Telegraph token, falling back to anonymous")
    t = Telegraph()
    try:
        t.create_account(short_name="Cholochhitro")
    except Exception:
        logger.exception("Failed to create Telegraph account")
    return t

telegraph = _init_telegraph()

# ==================== GLOBAL GUARDS ====================
_inflight: set = set()           # (chat_id, message_id) keys currently processing
_last_extract: dict = {}         # user_id -> last extract timestamp
EXTRACT_COOLDOWN = 8             # seconds between extractions per user


# ==================== HELPERS ====================
def format_track(lang: str | None, title: str | None) -> str:
    lang = (lang or "").strip()
    title = (title or "").strip()
    if lang and lang.lower() != "und":
        return lang
    if title:
        return title
    return "und"


def clean_title(file_name: str) -> str:
    """Strip extension and normalize separators for the Telegraph page title."""
    name = re.sub(r"\.(mkv|mp4|avi|mov|webm|m4v)$", "", file_name, flags=re.IGNORECASE)
    name = re.sub(r"[._\[\]()\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or "Media"


async def parse_tracks(client, log_msg, temp_path: str, lib_path):
    """Stream a header chunk and parse with MediaInfo. Retries with a bigger
    chunk limit if the first pass yields no real tracks (moov-at-end cases)."""
    last_info = None
    for limit in (5, 15):
        async with aiofiles.open(temp_path, "wb") as f:
            async for chunk in client.stream_media(log_msg, limit=limit):
                await f.write(chunk)

        info = await asyncio.wait_for(
            asyncio.to_thread(MediaInfo.parse, temp_path, library_file=lib_path),
            timeout=8,
        )
        last_info = info
        real = [t for t in info.tracks if (t.track_type or "").lower() != "general"]
        if real:
            return info
    return last_info


# ==================== HANDLERS ====================
@Client.on_callback_query(filters.regex(r"^wait_data$"), group=2)
async def wait_data_handler(client: Client, query: CallbackQuery):
    try:
        await query.answer("Still processing, please wait…", show_alert=False)
    except Exception:
        pass


@Client.on_callback_query(filters.regex(r"^extract_data"), group=2)
async def extract_data_handler(client: Client, query: CallbackQuery):
    # --- rate limit per user ---
    uid = query.from_user.id
    now = time.monotonic()
    if now - _last_extract.get(uid, 0) < EXTRACT_COOLDOWN:
        try:
            await query.answer("Wait a few seconds before another extraction.", show_alert=True)
        except Exception:
            pass
        return
    _last_extract[uid] = now

    # --- inflight guard on (chat_id, message_id) ---
    key = (query.message.chat.id, query.message.id)
    if key in _inflight:
        try:
            await query.answer("Already processing…", show_alert=False)
        except Exception:
            pass
        return
    _inflight.add(key)

    try:
        await query.answer("Fetching details…", show_alert=False)
    except Exception:
        pass

    # --- split safely ---
    try:
        if ":" in query.data:
            prefix, file_id = query.data.split(":", 1)
        elif "#" in query.data:
            prefix, file_id = query.data.split("#", 1)
        else:
            prefix, file_id = query.data, ""
    except ValueError:
        _inflight.discard(key)
        return

    current_markup = query.message.reply_markup
    wait_keyboard = []

    if current_markup and getattr(current_markup, "inline_keyboard", None):
        for row in current_markup.inline_keyboard:
            new_row = []
            for btn in row:
                if btn.callback_data == query.data:
                    new_row.append(
                        InlineKeyboardButton("ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ… ⏳", callback_data="wait_data")
                    )
                else:
                    new_row.append(btn)
            wait_keyboard.append(new_row)

    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(wait_keyboard)
        )
    except Exception:
        pass

    temp_path = os.path.join(
        tempfile.gettempdir(),
        f"acc_{uid}_{query.message.id}_{uuid.uuid4().hex}.tmp",
    )
    log_msg = None

    try:
        files_ = await get_file_details(file_id)
        if not files_:
            await query.message.reply_text("❌ File not found in DB.")
            return

        # --- get a streamable message ---
        if query.message and query.message.media:
            log_msg = query.message
        else:
            log_msg = await client.send_cached_media(
                chat_id=BIN_CHANNEL, file_id=file_id
            )

        file_name = get_name(log_msg)
        safe_title = clean_title(file_name)

        media_map = {
            "video": getattr(log_msg, "video", None),
            "document": getattr(log_msg, "document", None),
            "audio": getattr(log_msg, "audio", None),
            "animation": getattr(log_msg, "animation", None),
        }
        media = media_map.get(log_msg.media.value) if log_msg.media else None
        file_size = getattr(media, "file_size", 0) or 0

        lib_path = (
            os.path.abspath("MediaInfo.dll")
            if os.path.exists("MediaInfo.dll")
            else None
        )

        try:
            media_info = await parse_tracks(client, log_msg, temp_path, lib_path)
        except asyncio.TimeoutError:
            await query.message.reply_text("⚠️ Media parsing timed out. Try again.")
            return

        # --- extract tracks ---
        audio_tracks = []
        subtitle_tracks = []
        video_info = []
        seen_audio = set()
        seen_subs = set()

        for track in media_info.tracks:
            ttype = (track.track_type or "").lower()

            if ttype == "video":
                codec = track.format or track.codec_id or "Unknown"
                width = track.width or "?"
                height = track.height or "?"
                video_info.append(f"{codec} · {width}×{height}")

            elif ttype == "audio":
                lang = (
                    track.other_language[0]
                    if getattr(track, "other_language", None)
                    else track.language or "und"
                )
                k = (lang, track.title)
                if k not in seen_audio:
                    seen_audio.add(k)
                    audio_tracks.append({"language": lang, "title": track.title})

            elif ttype in ("text", "subtitle"):
                lang = (
                    track.other_language[0]
                    if getattr(track, "other_language", None)
                    else track.language or "und"
                )
                k = (lang, track.title)
                if k not in seen_subs:
                    seen_subs.add(k)
                    subtitle_tracks.append({"language": lang, "title": track.title})

        # ---------- BUILD PAGE ----------
        page_parts = []

        # Header
        page_parts.append("<h3>🎬 Media Info</h3>")
        page_parts.append("<p><i>Track listing extracted from the file</i></p>")

        # File panel
        size_mb = round(file_size / (1024 * 1024), 1) if file_size else 0
        if size_mb:
            page_parts.append(
                f"<p><b>📁 File</b><br>"
                f"<code>{file_name[:120]}</code><br>"
                f"<i>{size_mb} MB</i></p>"
            )
        else:
            page_parts.append(
                f"<p><b>📁 File</b><br>"
                f"<code>{file_name[:120]}</code></p>"
            )

        page_parts.append("<hr>")

        # Video
        page_parts.append("<h4>🎞️ Video</h4>")
        if video_info:
            for v in video_info:
                page_parts.append(f"<blockquote>{v}</blockquote>")
        else:
            page_parts.append("<p><i>No video track detected</i></p>")
        page_parts.append("<br>")

        # Audio
        if audio_tracks:
            page_parts.append(
                f"<h4>🎧 Audio · <code>{len(audio_tracks)}</code></h4>"
            )
            if len(audio_tracks) > 6:
                page_parts.append(
                    "<details><summary><b>Tap to expand</b></summary><ul>"
                )
                for a in audio_tracks:
                    page_parts.append(
                        f"<li>{format_track(a['language'], a['title'])}</li>"
                    )
                page_parts.append("</ul></details>")
            else:
                page_parts.append("<ul>")
                for a in audio_tracks:
                    page_parts.append(
                        f"<li>{format_track(a['language'], a['title'])}</li>"
                    )
                page_parts.append("</ul>")
        else:
            page_parts.append("<h4>🎧 Audio</h4>")
            page_parts.append("<p><i>No audio tracks detected</i></p>")
        page_parts.append("<br>")

        # Subtitles
        if subtitle_tracks:
            page_parts.append(
                f"<h4>💬 Subtitles · <code>{len(subtitle_tracks)}</code></h4>"
            )
            if len(subtitle_tracks) > 6:
                page_parts.append(
                    "<details><summary><b>Tap to expand</b></summary><ul>"
                )
                for s in subtitle_tracks:
                    page_parts.append(
                        f"<li>{format_track(s['language'], s['title'])}</li>"
                    )
                page_parts.append("</ul></details>")
            else:
                page_parts.append("<ul>")
                for s in subtitle_tracks:
                    page_parts.append(
                        f"<li>{format_track(s['language'], s['title'])}</li>"
                    )
                page_parts.append("</ul>")
        else:
            page_parts.append("<h4>💬 Subtitles</h4>")
            page_parts.append("<p><i>No subtitle tracks detected</i></p>")

        # Footer
        page_parts.append("<hr>")
        page_parts.append(
            '<p><i>Generated by '
            '<a href="https://t.me/Cholochhitro">Cholochhitro</a>'
            "</i></p>"
        )

        page_content = "".join(page_parts)

        # Telegraph hard cap ~64KB — truncate if huge
        if len(page_content) > 60000:
            page_content = page_content[:59000] + "<p><i>…truncated</i></p>"

        # ---------- CREATE PAGE ----------
        try:
            response = await asyncio.to_thread(
                telegraph.create_page,
                title=safe_title[:200],
                html_content=page_content,
                author_name="Cholochhitro",
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            await query.message.reply_text("⚠️ Telegraph is busy. Try again later.")
            return
        except Exception as e:
            logger.exception(e)
            await query.message.reply_text("⚠️ Failed to create info page.")
            return

        telegraph_url = response["url"]

        # ---------- SWAP BUTTON ----------
        success_keyboard = []
        if current_markup and getattr(current_markup, "inline_keyboard", None):
            for row in current_markup.inline_keyboard:
                new_row = []
                for btn in row:
                    if btn.callback_data == query.data or btn.callback_data == "wait_data":
                        new_row.append(
                            InlineKeyboardButton(
                                "📝 ᴠɪᴇᴡ ᴛʀᴀᴄᴋꜱ 📝", url=telegraph_url
                            )
                        )
                    else:
                        new_row.append(btn)
                success_keyboard.append(new_row)

        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(success_keyboard)
        )

    except Exception as e:
        logger.exception(e)
        try:
            await query.message.reply_text("⚠️ Something went wrong. Try again.")
        except Exception:
            pass

    finally:
        _inflight.discard(key)
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        # Clean up the streamable copy we pushed into BIN_CHANNEL,
        # but only if we created it (not the original query message).
        try:
            if (
                log_msg is not None
                and query.message
                and log_msg.id != query.message.id
                and log_msg.chat
                and log_msg.chat.id == BIN_CHANNEL
            ):
                await log_msg.delete()
        except Exception:
            pass
