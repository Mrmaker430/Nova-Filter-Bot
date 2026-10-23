import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault('API_ID', '12345')
os.environ.setdefault('API_HASH', 'abcdef1234567890abcdef1234567890')
os.environ.setdefault('BOT_TOKEN', '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11')
os.environ.setdefault('ADMINS', '12345678')
os.environ.setdefault('FILES_DATABASE_URL', 'mongodb://localhost:27017/files_db')
os.environ.setdefault('SECOND_FILES_DATABASE_URL', 'mongodb://localhost:27017/second_files_db')
os.environ.setdefault('DATA_DATABASE_URL', 'mongodb://localhost:27017/data_db')
os.environ.setdefault('LOG_CHANNEL', '-1001234567890')
os.environ.setdefault('BIN_CHANNEL', '-1001234567890')
os.environ.setdefault('URL', 'https://example.com/')
os.environ.setdefault('UPDATES_SEND_CHANNEL', '-1009999999999')

from utils import get_tv_season_episodes_info, send_update, _post_or_edit_update
from Script import script


class TestTVUpdates(unittest.TestCase):

    def test_get_tv_season_episodes_info_single_season(self):
        files = [
            {"file_name": "Stranger Things S01E01 1080p.mkv", "caption": ""},
            {"file_name": "Stranger Things S01E02 1080p.mkv", "caption": ""},
            {"file_name": "Stranger Things S01E08 1080p.mkv", "caption": ""},
        ]
        season_data, seasons_str, episodes_str = get_tv_season_episodes_info(files)
        self.assertEqual(seasons_str, "01")
        self.assertEqual(episodes_str, "S01 : 01 - 08")

    def test_get_tv_season_episodes_info_multi_seasons(self):
        files = [
            {"file_name": "Loki S01E01.mkv", "caption": ""},
            {"file_name": "Loki S01E06.mkv", "caption": ""},
            {"file_name": "Loki S02E01.mkv", "caption": ""},
            {"file_name": "Loki S02E06.mkv", "caption": ""},
            {"file_name": "Loki S03E01.mkv", "caption": ""},
            {"file_name": "Loki S04E10.mkv", "caption": ""},
        ]
        season_data, seasons_str, episodes_str = get_tv_season_episodes_info(files)
        self.assertEqual(seasons_str, "01-04")
        expected_episodes = (
            "S01 : 01 - 06\n"
            "S02 : 01 - 06\n"
            "S03 : 01 - 01\n"
            "S04 : 01 - 10"
        )
        self.assertEqual(episodes_str, expected_episodes)

    def test_get_tv_season_episodes_info_alternative_formats(self):
        files = [
            {"file_name": "Money Heist 01x04 720p.mkv", "caption": ""},
            {"file_name": "Money Heist Season 1 Episode 8.mkv", "caption": ""},
            {"file_name": "Money Heist S02E01-E10.mkv", "caption": ""},
        ]
        season_data, seasons_str, episodes_str = get_tv_season_episodes_info(files)
        self.assertEqual(seasons_str, "01-02")
        self.assertIn("S01 : 01 - 08", episodes_str)
        self.assertIn("S02 : 01 - 10", episodes_str)

    @patch('utils.get_poster')
    @patch('database.ia_filterdb.get_search_results')
    @patch('utils._post_or_edit_update', new_callable=AsyncMock)
    @patch('database.ia_filterdb.updates_collection.update_one', new_callable=AsyncMock)
    def test_send_update_tv_series(self, mock_db_update, mock_post, mock_get_search, mock_poster):
        mock_get_search.return_value = [
            {"file_name": "Loki S01E01.mkv", "caption": ""},
            {"file_name": "Loki S01E06.mkv", "caption": ""},
            {"file_name": "Loki S02E04.mkv", "caption": ""},
        ]
        mock_poster.return_value = {
            "title": "Loki",
            "kind": "tv",
            "votes": 100,
            "tmdb_id": 67195,
            "runtime": "52 min",
            "release_date": "2021-06-09",
            "year": "2021",
            "genres": "#Action, #SciFi",
            "plot": "Test plot",
            "rating": 8.2,
            "url": "https://www.themoviedb.org/tv/67195",
            "languages": "#English",
            "countries": "#USA",
            "poster": None,
            "backdrop": None,
            "logo": None
        }
        mock_post.return_value = 12345

        asyncio.run(send_update("Loki", "2021"))

        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        caption = call_args["text_or_caption"]
        self.assertIn("Loki", caption)
        self.assertIn("🔅 Sᴇᴀsᴏɴ : 01-02", caption)
        self.assertIn("🔹 Eᴘɪsᴏᴅᴇs :", caption)
        self.assertIn("S01 : 01 - 06", caption)
        self.assertIn("S02 : 01 - 04", caption)


if __name__ == '__main__':
    unittest.main()
