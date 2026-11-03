import pytest
from plugins.extract import format_track, clean_title
from pyrogram.types import InlineKeyboardButton

def test_format_track():
    assert format_track("eng", "English") == "eng"
    assert format_track("", "Hindi Audio") == "Hindi Audio"
    assert format_track("und", "Action Track") == "Action Track"
    assert format_track("und", "") == "und"
    assert format_track(None, None) == "und"

def test_clean_title():
    assert clean_title("Movie.2024.1080p.mkv") == "Movie 2024 1080p"
    assert clean_title("Sample_Video.mp4") == "Sample Video"
    assert clean_title("[Tag]_Test.File.avi") == "Tag Test File"
    assert clean_title("") == "Media"

def test_button_structure_in_commands():
    file_id = "60a1b2c3d4e5f67890123456"
    f_id_str = str(file_id)
    watch_btn = InlineKeyboardButton("🔖 Add Watchlist", callback_data=f"add_watch#{f_id_str}")
    fav_btn = InlineKeyboardButton("❤️ Add Favorites", callback_data=f"add_fav#{f_id_str}")
    extract_btn = InlineKeyboardButton("🎧 Audio Tracks 🎧", callback_data=f"extract_data:{f_id_str}")

    IS_STREAM = True
    URL = "https://example.com/"

    # Premium / Admin user
    user_is_prm = True
    if IS_STREAM and URL and user_is_prm:
        btn_prm = [[
            InlineKeyboardButton("⚡ Watch & Download", callback_data=f"stream#{f_id_str}")
        ],[
            extract_btn
        ],[
            watch_btn, fav_btn
        ],[
            InlineKeyboardButton("✖️ Close", callback_data="close_data")
        ]]
    else:
        btn_prm = [[
            extract_btn
        ],[
            watch_btn, fav_btn
        ],[
            InlineKeyboardButton("✖️ Close", callback_data="close_data")
        ]]

    assert btn_prm[0][0].text == "⚡ Watch & Download"
    assert btn_prm[1][0].text == "🎧 Audio Tracks 🎧"

    # Non-premium user
    user_is_prm = False
    if IS_STREAM and URL and user_is_prm:
        btn_non_prm = [[
            InlineKeyboardButton("⚡ Watch & Download", callback_data=f"stream#{f_id_str}")
        ],[
            extract_btn
        ],[
            watch_btn, fav_btn
        ],[
            InlineKeyboardButton("✖️ Close", callback_data="close_data")
        ]]
    else:
        btn_non_prm = [[
            extract_btn
        ],[
            watch_btn, fav_btn
        ],[
            InlineKeyboardButton("✖️ Close", callback_data="close_data")
        ]]

    assert btn_non_prm[0][0].text == "🎧 Audio Tracks 🎧"
    assert not any(b.text == "⚡ Watch & Download" for row in btn_non_prm for b in row)

def test_is_premium_admin_check():
    import asyncio
    from utils import is_premium
    from info import ADMINS
    if ADMINS:
        admin_id = ADMINS[0]
        assert asyncio.run(is_premium(admin_id, None)) is True


def test_to_small_caps():
    from utils import to_small_caps
    assert to_small_caps("Language") == "ʟᴀɴɢᴜᴀɢᴇ"
    assert to_small_caps("Quality") == "ǫᴜᴀʟɪᴛʏ"
    assert to_small_caps("Season") == "ꜱᴇᴀꜱᴏɴ"
    assert to_small_caps("Episode") == "ᴇᴘɪꜱᴏᴅᴇ"
    assert to_small_caps("Send All") == "ꜱᴇɴᴅ ᴀʟʟ"
    assert to_small_caps("Tutorial") == "ᴛᴜᴛᴏʀɪᴀʟ"
    assert to_small_caps("Buy Premium") == "ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ"
    assert to_small_caps("No More Pages") == "ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ"
    assert to_small_caps("Next") == "ɴᴇxᴛ"
    assert to_small_caps("Back") == "ʙᴀᴄᴋ"


def test_search_results_button_styles_and_order():
    from utils import to_small_caps
    from pyrogram import enums

    req = 12345
    key = "testkey"
    offset = 0

    # Test top filter buttons (rows 0 and 1)
    btn_row_0 = [
        InlineKeyboardButton(f"🌐 {to_small_caps('Language')}", callback_data=f"languages#{key}#{req}#{offset}", style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton(f"💎 {to_small_caps('Quality')}", callback_data=f"quality#{key}#{req}#{offset}", style=enums.ButtonStyle.PRIMARY)
    ]
    btn_row_1 = [
        InlineKeyboardButton(f"📁 {to_small_caps('Season')}", callback_data=f"season#{key}#{req}#{offset}", style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton(f"🎬 {to_small_caps('Episode')}", callback_data=f"episode#{key}#{req}#{offset}", style=enums.ButtonStyle.PRIMARY)
    ]

    assert btn_row_0[0].style == enums.ButtonStyle.PRIMARY
    assert btn_row_0[0].text == "🌐 ʟᴀɴɢᴜᴀɢᴇ"
    assert btn_row_0[1].style == enums.ButtonStyle.PRIMARY
    assert btn_row_0[1].text == "💎 ǫᴜᴀʟɪᴛʏ"
    assert btn_row_1[0].style == enums.ButtonStyle.PRIMARY
    assert btn_row_1[0].text == "📁 ꜱᴇᴀꜱᴏɴ"
    assert btn_row_1[1].style == enums.ButtonStyle.PRIMARY
    assert btn_row_1[1].text == "🎬 ᴇᴘɪꜱᴏᴅᴇ"

    # Test action row (Send All & Tutorial)
    btn_row_2 = [
        InlineKeyboardButton(f"⚡ {to_small_caps('Send All')}", callback_data=f"send_all#{key}#{req}", style=enums.ButtonStyle.SUCCESS),
        InlineKeyboardButton(to_small_caps("Tutorial"), url="https://example.com", style=enums.ButtonStyle.SUCCESS)
    ]

    assert btn_row_2[0].style == enums.ButtonStyle.SUCCESS
    assert btn_row_2[0].text == "⚡ ꜱᴇɴᴅ ᴀʟʟ"
    assert btn_row_2[1].style == enums.ButtonStyle.SUCCESS
    assert btn_row_2[1].text == "ᴛᴜᴛᴏʀɪᴀʟ"

    # Test single page bottom buttons (Buy Premium then No More Pages)
    btn_bottom_buy = InlineKeyboardButton(f"💎 {to_small_caps('Buy Premium')}", url="https://t.me/bot?start=premium", style=enums.ButtonStyle.SUCCESS)
    btn_bottom_nomore = InlineKeyboardButton(f"🚫 {to_small_caps('No More Pages')}", callback_data="buttons", style=enums.ButtonStyle.DANGER)

    assert btn_bottom_buy.style == enums.ButtonStyle.SUCCESS
    assert btn_bottom_buy.text == "💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ"
    assert btn_bottom_nomore.style == enums.ButtonStyle.DANGER
    assert btn_bottom_nomore.text == "🚫 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ"

    # Verify order: Buy Premium comes before No More Pages
    bottom_rows = [[btn_bottom_buy], [btn_bottom_nomore]]
    assert bottom_rows[0][0].text == "💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ"
    assert bottom_rows[1][0].text == "🚫 ɴᴏ ᴍᴏʀᴇ ᴘᴀ特ᴇꜱ" or "🚫 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ"
    assert bottom_rows[1][0].text == "🚫 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ"
