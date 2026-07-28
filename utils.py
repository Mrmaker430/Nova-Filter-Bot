from pyrogram.errors import UserNotParticipant, FloodWait
from info import FORCE_SUB_CHANNELS, LONG_IMDB_DESCRIPTION, ADMINS, IS_PREMIUM, TIME_ZONE, TMDB_API_KEY, USE_CAPTION_FILTER, UPDATES_SEND_CHANNEL, FILMS_LINK, REQUEST_FORCE_SUB_CHANNEL
import asyncio
import logging

logger = logging.getLogger(__name__)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from pyrogram import enums
import re
import string
from datetime import datetime
from database.users_chats_db import db
from shortzy import Shortzy
import requests, pytz
from Script import script

class SafeFormatter(string.Formatter):
    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            if key not in kwargs:
                return f"{{{key}}}"
            return kwargs[key]
        return super().get_value(key, args, kwargs)

    def format_field(self, value, format_spec):
        try:
            return super().format_field(value, format_spec)
        except Exception:
            return str(value)

def safe_format(template, **kwargs):
    formatter = SafeFormatter()
    try:
        return formatter.format(template, **kwargs)
    except Exception:
        return template


class temp(object):
    START_TIME = 0
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CANCEL = False
    U_NAME = None
    B_NAME = None
    SETTINGS = {}
    VERIFICATIONS = {}
    GET_ALL_FILES = {}
    USERS_CANCEL = False
    GROUPS_CANCEL = False
    BOT = None
    PREMIUM = {}
    QUERY_CACHE = {}


def get_plan_name(days):
    plan_names = {
        7: "1 Week",
        14: "2 Weeks",
        21: "3 Weeks",
        30: "1 Month",
        60: "2 Months",
        90: "3 Months",
        180: "6 Months",
        365: "1 Year"
    }
    if days in plan_names:
        return f"{plan_names[days]} Plan"
    return f"{days} Days Plan"


def format_hashtags(items_str):
    if not items_str or items_str == "N/A":
        return "N/A"
    items = [i.strip() for i in items_str.split(",") if i.strip()]
    hashtagged = []
    for item in items:
        clean_item = re.sub(r'[^a-zA-Z0-9_]', '', item)
        if clean_item:
            hashtagged.append(f"#{clean_item}")
    return ", ".join(hashtagged) if hashtagged else "N/A"


async def send_update(title, year, edit_msg_id=None):
    if not UPDATES_SEND_CHANNEL:
        return
    if not await db.get_movie_update_status():
        return
    btn = [[
        InlineKeyboardButton('📥 Request from Here 📥', url=FILMS_LINK, style=enums.ButtonStyle.SUCCESS)
    ]]
    data = await get_poster(f"{title} {year}")
    if not data:
        _year = f"({year})" if year else ""
        try:
            await temp.BOT.send_message(chat_id=UPDATES_SEND_CHANNEL, text=f"✅ New Added ✅\n\n🏷 Title: {title.title()} {_year}", reply_markup=InlineKeyboardMarkup(btn))
        except Exception as send_err:
            logger.error(f"Failed to send fallback message: {send_err}")
        try:
            await temp.BOT.send_sticker(
                chat_id=UPDATES_SEND_CHANNEL,
                sticker="CAACAgUAAxkBAALIC2poNkeCLO7oGxrvA-J9BuOkQgrdAAK0HgACcVWZVlDepbKeENKoPQQ"
            )
        except Exception as sticker_err:
            logger.error(f"Failed to send sticker: {sticker_err}")
        return

    # Genres and languages hashtag formatting
    genres_str = format_hashtags(data.get('genres'))
    languages_str = format_hashtags(data.get('languages'))

    # Rating formatting
    rating = data.get('rating')
    votes = data.get('votes')
    if rating and rating > 0:
        if isinstance(rating, (int, float)):
            if isinstance(rating, float) and rating.is_integer():
                rating_val = int(rating)
            else:
                rating_val = rating
            rating_str = f"{rating_val}/10"
        else:
            rating_str = f"{rating}/10"
        if votes:
            rating_str += f" ({votes} votes)"
    else:
        rating_str = "N/A"

    release_date = data.get('release_date') or "N/A"
    url = data.get('url')
    title_display = data.get('title') or title

    if data.get('kind') == 'tv':
        # Introduce 5-second sleep to let concurrent batch saves finish saving
        await asyncio.sleep(5)

        from database.ia_filterdb import get_search_results
        import PTN
        from plugins.pm_filter import get_seasons_from_filename, get_episodes_from_filename

        all_files = await get_search_results(title_display)

        def is_title_match(t1, t2):
            if not t1 or not t2:
                return False
            n1 = re.sub(r'[^a-z0-9]', '', t1.lower())
            n2 = re.sub(r'[^a-z0-9]', '', t2.lower())
            return n1 == n2 or n1 in n2 or n2 in n1

        matching_files = []
        for file_doc in all_files:
            fname = file_doc.get('file_name', '')
            p_data = PTN.parse(fname)
            p_title = p_data.get('title') or ""
            if is_title_match(p_title, title_display) or is_title_match(fname, title_display):
                matching_files.append((fname, p_data))

        seasons_dict = {}
        for fname, p_data in matching_files:
            seasons = get_seasons_from_filename(fname)
            if not seasons and 'season' in p_data:
                s = p_data['season']
                if isinstance(s, list):
                    seasons.update(s)
                elif isinstance(s, int):
                    seasons.add(s)
            if not seasons:
                seasons.add(1)
            for s_num in seasons:
                if s_num not in seasons_dict:
                    seasons_dict[s_num] = set()
                episodes = get_episodes_from_filename(fname, season=s_num)
                if not episodes and 'episode' in p_data:
                    e = p_data['episode']
                    if isinstance(e, list):
                        seasons_dict[s_num].update(e)
                    elif isinstance(e, int):
                        seasons_dict[s_num].add(e)
                else:
                    seasons_dict[s_num].update(episodes)

        if not seasons_dict:
            seasons_dict[1] = {1}

        total_episodes_count = sum(len(eps) for eps in seasons_dict.values())

        seasons_lines = []
        for s_num in sorted(seasons_dict.keys()):
            s_padded = f"{s_num:02d}"
            eps = sorted(list(seasons_dict[s_num]))
            max_ep = max(eps) if eps else 1
            seasons_lines.append(f"🔸 Season {s_padded} : Episode 01 to {max_ep:02d}")

        season_episode_block = "\n".join(seasons_lines)

        title_html = f"<b><a href='{url}'>{title_display}</a></b>" if url else f"<b>{title_display}</b>"
        caption = f"""✨ NEW UPLOAD ADDED ✨

📺 {title_html}
{season_episode_block}

🏷️ Category: #TV
⭐ Rating: {rating_str}
🎭 Genres: {genres_str}
🌐 Language: {languages_str}
📅 Release: {release_date}"""

    else:
        # Movie
        m_year = data.get('year') or year
        title_with_year = f"{title_display} ({m_year})" if m_year else title_display
        title_html = f"<b><a href='{url}'>{title_with_year}</a></b>" if url else f"<b>{title_with_year}</b>"
        caption = f"""✨ NEW UPLOAD ADDED ✨

🎬 {title_html}

🏷️ Category: #Movie
⭐ Rating: {rating_str}
🎭 Genres: {genres_str}
🌐 Language: {languages_str}
📅 Release: {release_date}"""

    poster_io = None
    try:
        from poster_generator import generate_movie_poster
        poster_io = await generate_movie_poster(data)
    except Exception as e:
        logger.exception(f"Failed to generate custom poster: {e}")

    msg = None
    if edit_msg_id:
        try:
            try:
                msg = await temp.BOT.edit_message_caption(
                    chat_id=UPDATES_SEND_CHANNEL,
                    message_id=edit_msg_id,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception:
                msg = await temp.BOT.edit_message_text(
                    chat_id=UPDATES_SEND_CHANNEL,
                    message_id=edit_msg_id,
                    text=caption,
                    reply_markup=InlineKeyboardMarkup(btn),
                    link_preview_options=LinkPreviewOptions(is_disabled=True)
                )
            logger.info(f"Successfully edited TV series update for message {edit_msg_id}")
        except Exception as edit_err:
            logger.error(f"Failed to edit TV series message {edit_msg_id}: {edit_err}. Falling back to sending a new post.")
            edit_msg_id = None

    if not edit_msg_id:
        try:
            if poster_io:
                msg = await temp.BOT.send_photo(chat_id=UPDATES_SEND_CHANNEL, photo=poster_io, caption=caption, reply_markup=InlineKeyboardMarkup(btn))
            elif data.get('poster'):
                msg = await temp.BOT.send_photo(chat_id=UPDATES_SEND_CHANNEL, photo=data.get('poster'), caption=caption, reply_markup=InlineKeyboardMarkup(btn))
            else:
                msg = await temp.BOT.send_message(chat_id=UPDATES_SEND_CHANNEL, text=caption, reply_markup=InlineKeyboardMarkup(btn), link_preview_options=LinkPreviewOptions(is_disabled=True))

            if msg:
                from database.ia_filterdb import updates_collection
                normalized_title = str(title).strip().lower()
                await updates_collection.update_one(
                    {"title": normalized_title, "year": year},
                    {"$set": {"message_id": msg.id, "kind": data.get('kind')}}
                )
        except Exception as send_err:
            logger.error(f"Failed to send movie update: {send_err}")

        try:
            await temp.BOT.send_sticker(
                chat_id=UPDATES_SEND_CHANNEL,
                sticker="CAACAgUAAxkBAALIC2poNkeCLO7oGxrvA-J9BuOkQgrdAAK0HgACcVWZVlDepbKeENKoPQQ"
            )
        except Exception as sticker_err:
            logger.error(f"Failed to send sticker: {sticker_err}")


async def handle_next_back(data, offset=0, max_results=0):
    out_data = data[offset:][:max_results]
    total_results = len(data)
    next_offset = offset + max_results
    if next_offset >= total_results:
        next_offset = 0
    return out_data, next_offset, total_results

async def is_subscribed(bot, query):
    btn = []
    user_id = query.from_user.id
    if FORCE_SUB_CHANNELS:
        for id in FORCE_SUB_CHANNELS.split(' '):
            chat = await bot.get_chat(int(id))
            try:
                member = await bot.get_chat_member(int(id), user_id)
                if member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
                    btn.append(
                        [InlineKeyboardButton(f'📢 Join : {chat.title}', url=chat.invite_link)]
                    )
            except UserNotParticipant:
                btn.append(
                    [InlineKeyboardButton(f'📢 Join : {chat.title}', url=chat.invite_link)]
                )
    if REQUEST_FORCE_SUB_CHANNEL and not await db.find_join_req(user_id):
        id = REQUEST_FORCE_SUB_CHANNEL
        chat = await bot.get_chat(int(id))
        try:
            member = await bot.get_chat_member(int(id), user_id)
            if member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
                url = await bot.create_chat_invite_link(int(id), creates_join_request=True)
                btn.append(
                    [InlineKeyboardButton(f'✨ Request : {chat.title}', url=url.invite_link)]
                )
        except UserNotParticipant:
            url = await bot.create_chat_invite_link(int(id), creates_join_request=True)
            btn.append(
                [InlineKeyboardButton(f'✨ Request : {chat.title}', url=url.invite_link)]
            )
    return btn


def upload_image(file_path):
    with open(file_path, 'rb') as f:
        files = {'files[]': f}
        response = requests.post("https://uguu.se/upload", files=files)

    if response.status_code == 200:
        try:
            data = response.json()
            return data['files'][0]['url'].replace('\\/', '/')
        except Exception as e:
            return None
    else:
        return None


def list_to_str(k):
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    else:
        return ", ".join(str(i) for i in k)


async def get_poster(query, bulk=False, id=False, file=None):
    if not TMDB_API_KEY:
        return None
    TMDB_BASE = "https://api.themoviedb.org/3"

    year = None
    title = query

    if not id:
        query = query.strip()
        query = re.sub(r'\b(?:s(?:eason)?\s*\d+\s*(?:e(?:p(?:isode)?)?\s*\d+)?|e(?:p(?:isode)?)?\s*\d+)\b', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\b(?:to|and|season|episode|ep|eps|seasons)\b', '', query, flags=re.IGNORECASE)
        query = re.sub(r'[\s\.\-_]+$', '', query)
        query = re.sub(r'^[\s\.\-_]+', '', query)
        query = re.sub(r'\s+', ' ', query).strip()

        year_match = re.findall(r"[1-2]\d{3}$", query)
        if year_match:
            year = year_match[0]
            title = query.replace(year, "").strip()
        else:
            title = query

        if not year_match and file:
            file_year = re.findall(r"[1-2]\d{3}", file)
            if file_year:
                year = file_year[0]

        url = f"{TMDB_BASE}/search/multi"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title
        }

        res = requests.get(url, params=params).json()

        results = [
            r for r in res.get("results", [])
            if r.get("media_type") in ["movie", "tv"]
        ]

        if not results:
            return None

        if year:
            filtered = []
            for r in results:
                release = r.get("release_date") or r.get("first_air_date")
                if release and release.startswith(str(year)):
                    filtered.append(r)

            if filtered:
                results = filtered

        if bulk:
            _bulk = []
            for r in results:
                _title = r.get("title") or r.get("name")
                if _title:
                    _bulk.append({
                        "title": _title,
                        "id": r["id"]
                        })
            return _bulk


        data = results[0]
        tmdb_id = data["id"]
        media_type = data["media_type"]

    else:
        tmdb_id = query

        movie_test = requests.get(
            f"{TMDB_BASE}/movie/{tmdb_id}",
            params={"api_key": TMDB_API_KEY}
        )

        if movie_test.status_code == 200:
            media_type = "movie"
            data = movie_test.json()
        else:
            media_type = "tv"
            data = requests.get(
                f"{TMDB_BASE}/tv/{tmdb_id}",
                params={"api_key": TMDB_API_KEY}
            ).json()

    if not id:
        data = requests.get(
            f"{TMDB_BASE}/{media_type}/{tmdb_id}",
            params={"api_key": TMDB_API_KEY}
        ).json()

    title = data.get("title") or data.get("name")

    poster = None
    if data.get("poster_path"):
        poster = f"https://image.tmdb.org/t/p/original{data['poster_path']}"

    backdrop = None
    if data.get("backdrop_path"):
        backdrop = f"https://image.tmdb.org/t/p/original{data['backdrop_path']}"
    elif data.get("poster_path"):
        backdrop = f"https://image.tmdb.org/t/p/original{data['poster_path']}"

    seasons = data.get("number_of_seasons") if media_type == "tv" else None

    release_date = data.get("release_date") or data.get("first_air_date")

    genres = list_to_str([g["name"] for g in data.get("genres", [])])

    runtime = None
    if media_type == "movie":
        runtime = data.get("runtime")
    else:
        runtime = list_to_str(data.get("episode_run_time"))

    plot = data.get("overview") if LONG_IMDB_DESCRIPTION else str(data.get("overview"))[:200]

    rating = data.get("vote_average")
    votes = data.get("vote_count")
    languages = list_to_str([l["english_name"] for l in data.get("spoken_languages", [])])
    countries = list_to_str([c["name"] for c in data.get("production_countries", [])])

    return {
        "title": title,
        "tmdb_id": tmdb_id,
        "kind": media_type,
        "languages": languages,
        "countries": countries,
        "release_date": release_date,
        "year": release_date[:4] if release_date else None,
        "genres": genres,
        "runtime": runtime,
        "rating": rating,
        "votes": votes,
        "poster": poster,
        "backdrop": backdrop,
        "seasons": seasons,
        "plot": plot,
        "url": f"https://www.themoviedb.org/{media_type}/{tmdb_id}"
    }

async def is_check_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False

async def get_verify_status(user_id):
    verify = temp.VERIFICATIONS.get(user_id)
    if not verify:
        verify = await db.get_verify_status(user_id)
        temp.VERIFICATIONS[user_id] = verify
    return verify

async def update_verify_status(user_id, verify_token="", is_verified=False, link="", expire_time=0):
    current = await get_verify_status(user_id)
    current['verify_token'] = verify_token
    current['is_verified'] = is_verified
    current['link'] = link
    current['expire_time'] = expire_time
    temp.VERIFICATIONS[user_id] = current
    await db.update_verify_status(user_id, current)

    
async def is_premium(user_id, bot):
    if not IS_PREMIUM:
        return True
    if user_id in ADMINS:
        return True
    mp = await db.get_plan(user_id)
    if mp['premium']:
        if mp['expire'] < datetime.now():
            await bot.send_message(user_id, f"⏳ <b>VIP Premium Expiring Soon!</b>\n\n<blockquote>👑 Your <b>{mp['plan']}</b> VIP Premium access will expire on <code>{mp['expire'].strftime('%Y.%m.%d %H:%M:%S')}</code>. Please use /plan to renew your subscription and maintain uninterrupted ad-free service!</blockquote>")
            mp['expire'] = ''
            mp['plan'] = ''
            mp['premium'] = False
            await db.update_plan(user_id, mp)
            return False
        return True
    else:
        return False


async def check_premium(bot):
    while True:
        pr = [i for i in await db.get_premium_users() if i['status']['premium']]
        for p in pr:
            mp = p['status']
            if mp['expire'] < datetime.now():
                try:
                    await bot.send_message(
                        p['id'],
                        f"⏳ <b>VIP Premium Expiring Soon!</b>\n\n<blockquote>👑 Your <b>{mp['plan']}</b> VIP Premium access will expire on <code>{mp['expire'].strftime('%Y.%m.%d %H:%M:%S')}</code>. Please use /plan to renew your subscription and maintain uninterrupted ad-free service!</blockquote>"
                    )
                except Exception:
                    pass
                mp['expire'] = ''
                mp['plan'] = ''
                mp['premium'] = False
                await db.update_plan(p['id'], mp)
        await asyncio.sleep(1200)


async def broadcast_messages(user_id, message, pin):
    try:
        m = await message.copy(chat_id=user_id)
        if pin:
            await m.pin(both_sides=True)
        return "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message, pin)
    except Exception as e:
        await db.delete_user(int(user_id))
        return "Error"

async def groups_broadcast_messages(chat_id, message, pin):
    try:
        k = await message.copy(chat_id=chat_id)
        if pin:
            try:
                await k.pin()
            except:
                pass
        return "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await groups_broadcast_messages(chat_id, message, pin)
    except Exception as e:
        await db.delete_chat(chat_id)
        return "Error"

async def get_settings(group_id):
    settings = temp.SETTINGS.get(group_id)
    if not settings:
        settings = await db.get_settings(group_id)
        temp.SETTINGS.update({group_id: settings})
    return settings
    
async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current.update({key: value})
    temp.SETTINGS.update({group_id: current})
    await db.update_settings(group_id, current)

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])


async def get_shortlink(url, api, link):
    shortzy = Shortzy(api_key=api, base_site=url)
    link = await shortzy.convert(link)
    return link

def get_readable_time(seconds):
    periods = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result

def get_wish():
    time = datetime.now(pytz.timezone(TIME_ZONE))
    now = time.strftime("%H")
    if now < "12":
        status = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞"
    elif now < "18":
        status = "ɢᴏᴏᴅ ᴀꜰᴛᴇʀɴᴏᴏɴ 🌗"
    else:
        status = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 🌘"
    return status
    
async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:]
        if value:
            value = int(value)
        return value, unit
    value, unit = extract_value_and_unit(time_string)
    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0


async def render_list_page(client, query_or_msg, user_id, list_type="watchlist", page=0, edit=False):
    if list_type == "favorites":
        items = await db.get_favorites(user_id)
        title = "❤️ <b>Your Favorites List</b>"
        empty_text = "💔 <b>Your Favorites list is currently empty!</b>\n\nClick on <b>❤️ Favorites</b> when viewing any file to save it here for quick access later."
        del_cb_prefix = "del_fav"
        page_cb_prefix = "favorites_page"
        clear_cb = "clear_all_favorites"
        clear_text = "🗑️ Clear All Favorites"
    else:
        items = await db.get_watchlist(user_id)
        title = "🔖 <b>Your Watchlist</b>"
        empty_text = "📂 <b>Your Watchlist is currently empty!</b>\n\nClick on <b>🔖 Watchlist</b> when viewing any file to save it here for quick access later."
        del_cb_prefix = "del_watch"
        page_cb_prefix = "watchlist_page"
        clear_cb = "clear_all_watchlist"
        clear_text = "🗑️ Clear All Watchlist"
        
    if not items:
        buttons = [[InlineKeyboardButton("✖️ Close", callback_data="close_data")]]
        if edit:
            return await query_or_msg.edit_message_text(empty_text, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            return await query_or_msg.reply_text(empty_text, reply_markup=InlineKeyboardMarkup(buttons))
    
    total_files = len(items)
    total_pages = (total_files + 9) // 10
    if page >= total_pages:
        page = max(0, total_pages - 1)
        
    start_idx = page * 10
    end_idx = min(start_idx + 10, total_files)
    
    current_ids = items[start_idx:end_idx]
    buttons = []
    from database.ia_filterdb import get_file_details
    
    for f_id in current_ids:
        file_info = await get_file_details(f_id)
        if not file_info:
            buttons.append([
                InlineKeyboardButton("⚠️ [Deleted/Missing File]", callback_data=f"file#{f_id}"),
                InlineKeyboardButton("✖️", callback_data=f"{del_cb_prefix}#{f_id}#list#{page}")
            ])
            continue
        fname = file_info.get('file_name', 'Unknown')
        fsize = get_size(file_info.get('file_size', 0))
        buttons.append([
            InlineKeyboardButton(f"📁 [{fsize}] {fname[:35]}", callback_data=f"file#{f_id}"),
            InlineKeyboardButton("✖️", callback_data=f"{del_cb_prefix}#{f_id}#list#{page}")
        ])
        
    page_buttons = []
    if page > 0:
        page_buttons.append(InlineKeyboardButton("🔙 Back", callback_data=f"{page_cb_prefix}#{page - 1}"))
    page_buttons.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
    if end_idx < total_files:
        page_buttons.append(InlineKeyboardButton("⏭️ Next", callback_data=f"{page_cb_prefix}#{page + 1}"))
    if len(page_buttons) > 1:
        buttons.append(page_buttons)
        
    buttons.append([InlineKeyboardButton(clear_text, callback_data=clear_cb)])
    buttons.append([InlineKeyboardButton("✖️ Close", callback_data="close_data")])
    
    text = f"{title} (<b>{total_files} Files</b>)\n\n<blockquote>💡 Click any file below to get it instantly, or click ✖️ to remove it from your list.</blockquote>"
    
    if edit:
        await query_or_msg.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query_or_msg.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


