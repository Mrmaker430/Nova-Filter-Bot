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
    # Simulate button construction for single file
    file_id = "60a1b2c3d4e5f67890123456"
    f_id_str = str(file_id)
    watch_btn = InlineKeyboardButton("🔖 Add Watchlist", callback_data=f"add_watch#{f_id_str}")
    fav_btn = InlineKeyboardButton("❤️ Add Favorites", callback_data=f"add_fav#{f_id_str}")
    extract_btn = InlineKeyboardButton("🎧 Audio Tracks 🎧", callback_data=f"extract_data:{f_id_str}")

    btn = [[
        InlineKeyboardButton("⚡ Watch & Download", callback_data=f"stream#{f_id_str}")
    ],[
        extract_btn
    ],[
        watch_btn, fav_btn
    ],[
        InlineKeyboardButton("✖️ Close", callback_data="close_data")
    ]]

    assert btn[0][0].text == "⚡ Watch & Download"
    assert btn[1][0].text == "🎧 Audio Tracks 🎧"
    assert btn[1][0].callback_data == f"extract_data:{f_id_str}"
