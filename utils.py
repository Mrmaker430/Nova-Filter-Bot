from pyrogram.errors import UserNotParticipant, FloodWait
from info import FORCE_SUB_CHANNELS, LONG_IMDB_DESCRIPTION, ADMINS, IS_PREMIUM, TIME_ZONE, TMDB_API_KEY, USE_CAPTION_FILTER, UPDATES_SEND_CHANNEL, FILMS_LINK, REQUEST_FORCE_SUB_CHANNEL
import asyncio, os, io, tempfile
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from pyrogram import enums
import re
from datetime import datetime
from database.users_chats_db import db
from shortzy import Shortzy
import aiohttp, pytz
from Script import script


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
    SPELL_CHECK = {}
    GROUPS_CANCEL = False
    BOT = None
    PREMIUM = {}


SMALL_CAPS_TRANS = str.maketrans(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
)

def to_small_caps(text: str) -> str:
    if not text:
        return ""
    return str(text).translate(SMALL_CAPS_TRANS)


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


async def send_update(title, year):
    if not UPDATES_SEND_CHANNEL:
        return
    btn = [[
        InlineKeyboardButton('📥 Request from Here 📥', url=FILMS_LINK)
    ]]
    data = await get_poster(f"{title} {year}")
    if not data:
        _year = f"({year})" if year else ""
        await temp.BOT.send_message(chat_id=UPDATES_SEND_CHANNEL, text=f"✅ New Added ✅\n\n🏷 Title: {title.title()} {_year}", reply_markup=InlineKeyboardMarkup(btn))
        return
    caption = script.NEW_ADDED_TEMPLATE.format(
        title=data['title'],
        kind=data['kind'],
        votes=data['votes'],
        tmdb_id=data["tmdb_id"],
        runtime=data["runtime"],
        release_date=data['release_date'],
        year=data['year'],
        genres=data['genres'],
        plot=data['plot'],
        rating=data['rating'],
        url=data['url'],
        languages=data['languages'],
        countries=data['countries']
    )
    
    poster_path = await generate_poster_image(data)
    photo = poster_path if poster_path else data.get('poster')
    if photo:
        try:
            await temp.BOT.send_photo(chat_id=UPDATES_SEND_CHANNEL, photo=photo, caption=caption, reply_markup=InlineKeyboardMarkup(btn))
        finally:
            if poster_path and os.path.exists(poster_path):
                try:
                    os.remove(poster_path)
                except Exception:
                    pass
    else:
        await temp.BOT.send_message(chat_id=UPDATES_SEND_CHANNEL, text=caption, reply_markup=InlineKeyboardMarkup(btn), link_preview_options=LinkPreviewOptions(is_disabled=True))


async def handle_next_back(data, offset=0, max_results=0):
    out_data = data[offset:][:max_results]
    total_results = len(data)
    next_offset = offset + max_results
    if next_offset >= total_results:
        next_offset = 0
    return out_data, next_offset, total_results

async def is_subscribed(bot, query):
    btn = []
    if await is_premium(query.from_user.id, bot):
        return btn
    fsub = await db.get_fsub()
    fsub_channels = fsub if fsub else FORCE_SUB_CHANNELS
    if fsub_channels:
        for id in fsub_channels.split(' '):
            if not id.strip():
                continue
            try:
                chat = await bot.get_chat(int(id))
                try:
                    await bot.get_chat_member(int(id), query.from_user.id)
                except UserNotParticipant:
                    invite_link = chat.invite_link or f"https://t.me/c/{str(id).replace('-100', '')}"
                    btn.append(
                        [InlineKeyboardButton(f'📢 Join : {chat.title}', url=invite_link)]
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error checking fsub for channel {id}: {e}")

    req_fsub = await db.get_req_fsub()
    req_fsub_channel = req_fsub if req_fsub else REQUEST_FORCE_SUB_CHANNEL
    if req_fsub_channel:
        for id in req_fsub_channel.split(' '):
            if not id.strip():
                continue
            try:
                if not await db.find_join_req(query.from_user.id, int(id)):
                    chat = await bot.get_chat(int(id))
                    try:
                        await bot.get_chat_member(int(id), query.from_user.id)
                    except UserNotParticipant:
                        url = await bot.create_chat_invite_link(int(id), creates_join_request=True)
                        btn.append(
                            [InlineKeyboardButton(f'✨ Request : {chat.title}', url=url.invite_link)]
                        )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error checking req_fsub for channel {id}: {e}")
    return btn


async def upload_image(file_path):
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('files[]', f)
                async with session.post("https://uguu.se/upload", data=data) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        return res_json['files'][0]['url'].replace('\\/', '/')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error uploading image: {e}")
    return None


async def get_poster(query):
    if not TMDB_API_KEY:
        return None
    TMDB_BASE = "https://api.themoviedb.org/3"

    query = query.strip()
    
    import PTN
    
    parsed = PTN.parse(query)
    title = parsed.get("title", query)
    year = parsed.get("year", None)

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = f"{TMDB_BASE}/search/multi"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title
        }
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                res = await resp.json()
        except Exception:
            return None

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

        data = results[0]
        tmdb_id = data["id"]
        media_type = data["media_type"]

        try:
            async with session.get(
                f"{TMDB_BASE}/{media_type}/{tmdb_id}",
                params={"api_key": TMDB_API_KEY}
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except Exception:
            return None

        title = data.get("title") or data.get("name")

        poster = None
        if data.get("poster_path"):
            poster = f"https://image.tmdb.org/t/p/original{data['poster_path']}"

        backdrop = None
        if data.get("backdrop_path"):
            backdrop = f"https://image.tmdb.org/t/p/w1280{data['backdrop_path']}"

        logo = None
        try:
            async with session.get(
                f"{TMDB_BASE}/{media_type}/{tmdb_id}/images",
                params={"api_key": TMDB_API_KEY, "include_image_language": "en,null"}
            ) as resp:
                if resp.status == 200:
                    img_res = await resp.json()
                    logos = img_res.get("logos", [])
                    if logos:
                        en_logos = [l for l in logos if l.get("iso_639_1") == "en"]
                        selected_logo = en_logos[0] if en_logos else logos[0]
                        if selected_logo.get("file_path"):
                            logo = f"https://image.tmdb.org/t/p/w500{selected_logo['file_path']}"
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error fetching tmdb logo: {e}")

    release_date = data.get("release_date") or data.get("first_air_date") or "N/A"

    genres_list = data.get("genres", [])
    genres = ", ".join([f"#{g['name'].title().replace(' ', '').replace('-', '')}" for g in genres_list]) if genres_list else "N/A"

    if media_type == "movie":
        runtime_val = data.get("runtime")
    else:
        ep_rt = data.get("episode_run_time")
        runtime_val = ep_rt[0] if ep_rt else None
    runtime = f"{runtime_val} min" if runtime_val else "N/A"

    plot = data.get("overview")
    plot = plot if LONG_IMDB_DESCRIPTION else (str(plot)[:200] if plot else "N/A")

    rating = data.get("vote_average") or "N/A"
    votes = data.get("vote_count") or "N/A"

    langs_list = data.get("spoken_languages", [])
    languages = ", ".join([f"#{l['english_name'].title().replace(' ', '').replace('-', '')}" for l in langs_list]) if langs_list else "N/A"

    countries_list = data.get("production_countries", [])
    countries = ", ".join([f"#{c['name'].title().replace(' ', '').replace('-', '')}" for c in countries_list]) if countries_list else "N/A"

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
        "logo": logo,
        "plot": plot,
        "url": f"https://www.themoviedb.org/{media_type}/{tmdb_id}"
    }


def _render_poster_canvas(data, backdrop_bytes, poster_bytes, logo_bytes, channel_handle):
    if not data:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont

        if not channel_handle:
            channel_handle = "@cholochhitro"
        if not channel_handle.startswith("@"):
            channel_handle = f"@{channel_handle}"

        W, H = 1920, 1080
        canvas = Image.new("RGBA", (W, H), (15, 15, 15, 255))

        # 1. Backdrop Image
        if backdrop_bytes:
            try:
                bg = Image.open(io.BytesIO(backdrop_bytes)).convert("RGBA")
                bg_ratio = bg.width / bg.height
                target_ratio = W / H
                if bg_ratio > target_ratio:
                    new_w = int(H * bg_ratio)
                    bg = bg.resize((new_w, H), Image.Resampling.LANCZOS)
                    left = (new_w - W) // 2
                    bg = bg.crop((left, 0, left + W, H))
                else:
                    new_h = int(W / bg_ratio)
                    bg = bg.resize((W, new_h), Image.Resampling.LANCZOS)
                    top = (new_h - H) // 2
                    bg = bg.crop((0, top, W, top + H))
                canvas.paste(bg, (0, 0))
            except Exception:
                pass

        # 2. Mini Poster (Bottom Left)
        poster_w, poster_h = 330, 490
        poster_x, poster_y = 75, H - poster_h - 75

        if poster_bytes:
            try:
                p_img = Image.open(io.BytesIO(poster_bytes)).convert("RGBA")
                p_img = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)

                radius = 28
                mask = Image.new("L", (poster_w, poster_h), 0)
                draw_m = ImageDraw.Draw(mask)
                draw_m.rounded_rectangle([(0, 0), (poster_w, poster_h)], radius=radius, fill=255)

                border_img = Image.new("RGBA", (poster_w + 8, poster_h + 8), (255, 255, 255, 230))
                b_mask = Image.new("L", (poster_w + 8, poster_h + 8), 0)
                draw_bm = ImageDraw.Draw(b_mask)
                draw_bm.rounded_rectangle([(0, 0), (poster_w + 8, poster_h + 8)], radius=radius + 4, fill=255)

                canvas.paste(border_img, (poster_x - 4, poster_y - 4), b_mask)
                canvas.paste(p_img, (poster_x, poster_y), mask)
            except Exception:
                pass

        content_x = poster_x + poster_w + 55
        content_max_w = W - content_x - 80

        # 3. Logo Title
        logo_placed = False
        logo_y = poster_y + 10
        logo_max_h = 160

        if logo_bytes:
            try:
                l_img = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
                l_w, l_h = l_img.size
                scale = min(content_max_w / l_w, logo_max_h / l_h)
                new_lw = int(l_w * scale)
                new_lh = int(l_h * scale)
                l_img = l_img.resize((new_lw, new_lh), Image.Resampling.LANCZOS)

                canvas.paste(l_img, (content_x, logo_y), l_img)
                logo_placed = True
                badge_y = logo_y + new_lh + 35
            except Exception:
                pass

        # Fonts
        font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        try:
            b_font = ImageFont.truetype(font_bold_path, 24)
            plot_font = ImageFont.truetype(font_bold_path, 28)
            title_font = ImageFont.truetype(font_bold_path, 68)
        except Exception:
            b_font = ImageFont.load_default()
            plot_font = ImageFont.load_default()
            title_font = ImageFont.load_default()

        if not logo_placed:
            draw = ImageDraw.Draw(canvas)
            title_text = str(data.get('title', '')).upper()
            draw.text((content_x, logo_y), title_text, font=title_font, fill=(255, 255, 255, 255))
            badge_y = logo_y + 90

        # 4. Badges / Pills Row
        draw = ImageDraw.Draw(canvas)
        curr_x = content_x
        b_height = 48
        b_radius = 12

        # 4a. Rating Badge
        rating_val = str(data.get('rating', 'N/A'))
        if rating_val != 'N/A':
            try:
                rating_val = str(round(float(rating_val), 1))
            except Exception:
                pass
        star_txt = f"★ {rating_val}"
        star_bbox = b_font.getbbox(star_txt)
        star_w = star_bbox[2] - star_bbox[0] + 30
        draw.rounded_rectangle([(curr_x, badge_y), (curr_x + star_w, badge_y + b_height)], radius=b_radius, fill=(30, 30, 30, 230))
        draw.text((curr_x + 15, badge_y + 10), "★", font=b_font, fill=(255, 193, 7, 255))
        draw.text((curr_x + 42, badge_y + 10), rating_val, font=b_font, fill=(255, 255, 255, 255))
        curr_x += star_w + 18

        # 4b. IMDb Badge
        imdb_txt = "IMDb"
        imdb_bbox = b_font.getbbox(imdb_txt)
        imdb_w = imdb_bbox[2] - imdb_bbox[0] + 30
        draw.rounded_rectangle([(curr_x, badge_y), (curr_x + imdb_w, badge_y + b_height)], radius=b_radius, fill=(226, 182, 22, 255))
        draw.text((curr_x + 15, badge_y + 10), imdb_txt, font=b_font, fill=(0, 0, 0, 255))
        curr_x += imdb_w + 18

        # 4c. Year Badge
        year_val = str(data.get('year', '') or '')
        if year_val:
            year_bbox = b_font.getbbox(year_val)
            year_w = year_bbox[2] - year_bbox[0] + 30
            draw.rounded_rectangle([(curr_x, badge_y), (curr_x + year_w, badge_y + b_height)], radius=b_radius, fill=(229, 9, 20, 255))
            draw.text((curr_x + 15, badge_y + 10), year_val, font=b_font, fill=(255, 255, 255, 255))
            curr_x += year_w + 18

        # 4d. Genre Badge
        genres_raw = data.get('genres', '')
        first_genre = 'DRAMA'
        if '#' in str(genres_raw):
            first_genre = str(genres_raw).split('#')[1].split(',')[0].strip().upper()
        elif genres_raw and genres_raw != 'N/A':
            first_genre = str(genres_raw).split(',')[0].strip().upper()
        genre_bbox = b_font.getbbox(first_genre)
        genre_w = genre_bbox[2] - genre_bbox[0] + 30
        draw.rounded_rectangle([(curr_x, badge_y), (curr_x + genre_w, badge_y + b_height)], radius=b_radius, fill=(230, 81, 0, 255))
        draw.text((curr_x + 15, badge_y + 10), first_genre, font=b_font, fill=(255, 255, 255, 255))
        curr_x += genre_w + 18

        # 4e. Channel Badge
        chn_txt = f"✈ {channel_handle}"
        chn_bbox = b_font.getbbox(chn_txt)
        chn_w = chn_bbox[2] - chn_bbox[0] + 30
        draw.rounded_rectangle([(curr_x, badge_y), (curr_x + chn_w, badge_y + b_height)], radius=b_radius, fill=(0, 136, 204, 255))
        draw.text((curr_x + 15, badge_y + 10), chn_txt, font=b_font, fill=(255, 255, 255, 255))

        # 5. Plot / Overview
        plot_y = badge_y + b_height + 30
        plot_text = str(data.get('plot', '') or '')
        if plot_text and plot_text != 'N/A':
            words = plot_text.split()
            lines = []
            curr_line = ""
            for w in words:
                test_line = f"{curr_line} {w}".strip()
                test_w = plot_font.getbbox(test_line)[2] - plot_font.getbbox(test_line)[0]
                if test_w <= content_max_w:
                    curr_line = test_line
                else:
                    lines.append(curr_line)
                    curr_line = w
                    if len(lines) >= 2:
                        break
            if curr_line and len(lines) < 3:
                if len(lines) == 2 and len(words) > len(" ".join(lines).split()):
                    lines.append(curr_line + "...")
                else:
                    lines.append(curr_line)

            line_y = plot_y
            for l in lines[:3]:
                draw.text((content_x, line_y), l, font=plot_font, fill=(240, 240, 240, 240))
                line_y += 42

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        output_path = temp_file.name
        temp_file.close()

        rgb_canvas = canvas.convert("RGB")
        rgb_canvas.save(output_path, quality=95)
        return output_path
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating poster image: {e}")
        return None


async def generate_poster_image(data, channel_handle=None):
    if not data:
        return None
    async def _fetch_bytes(session, url):
        if not url:
            return None
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception:
            pass
        return None

    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        backdrop_bytes = await _fetch_bytes(session, data.get('backdrop'))
        poster_bytes = await _fetch_bytes(session, data.get('poster'))
        logo_bytes = await _fetch_bytes(session, data.get('logo'))

    return await asyncio.to_thread(
        _render_poster_canvas, data, backdrop_bytes, poster_bytes, logo_bytes, channel_handle
    )

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
        return False
    if user_id in ADMINS:
        return True
    mp = await db.get_plan(user_id)
    if mp['premium']:
        if mp['expire'] < datetime.now():
            await bot.send_message(user_id, f"⏳ <b>VIP Premium Expired!</b>\n\n<blockquote>👑 Your <b>{mp['plan']}</b> VIP Premium access will expire on <code>{mp['expire'].strftime('%Y.%m.%d %H:%M:%S')}</code>. Please use /plan to renew your subscription and maintain uninterrupted ad-free service!</blockquote>")
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
                        f"⏳ <b>VIP Premium Expired!</b>\n\n<blockquote>👑 Your <b>{mp['plan']}</b> VIP Premium access will expire on <code>{mp['expire'].strftime('%Y.%m.%d %H:%M:%S')}</code>. Please use /plan to renew your subscription and maintain uninterrupted ad-free service!</blockquote>"
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
    return '-' if result == '' else result

def get_wish():
    time = datetime.now(pytz.timezone(TIME_ZONE))
    now = time.strftime("%H")
    if now < "12":
        status = "🌅 Good morning 🌞"
    elif now < "18":
        status = "🌤️ Good afternoon 🌗"
    else:
        status = "🌙 Good evening 🌘"
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



async def get_imdb_suggestions(query):
    try:
        from urllib.parse import quote
        import aiohttp
        url = f'https://v3.sg.media-imdb.com/suggestion/x/{quote(query.lower())}.json'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for d in data.get('d', []):
                        if d.get('q') in ['feature', 'TV series', 'TV mini-series', 'TV movie', 'video', 'short', 'TV special', 'TV short', 'documentary']:
                            title = d.get('l')
                            year = d.get('y')
                            if year:
                                title = f"{title} ({year})"
                            results.append({
                                'title': title,
                                'id': d.get('id')
                            })
                    return results
    except Exception as e:
        print(f"IMDb suggest error: {e}")
    return []
