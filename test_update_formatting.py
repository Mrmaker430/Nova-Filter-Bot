import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from utils import format_hashtags, send_update

class TestUpdateFormatting(unittest.IsolatedAsyncioTestCase):
    def test_format_hashtags(self):
        # Normal inputs
        self.assertEqual(format_hashtags("Comedy, Drama"), "#Comedy, #Drama")
        self.assertEqual(format_hashtags("Malayalam, Tamil"), "#Malayalam, #Tamil")
        self.assertEqual(format_hashtags("Korean"), "#Korean")
        self.assertEqual(format_hashtags("Sci-Fi, Action & Adventure"), "#SciFi, #ActionAdventure")

        # Edge cases
        self.assertEqual(format_hashtags(""), "N/A")
        self.assertEqual(format_hashtags(None), "N/A")
        self.assertEqual(format_hashtags("N/A"), "N/A")

    @patch('utils.get_poster')
    @patch('utils.db.get_movie_update_status', new_callable=AsyncMock)
    @patch('utils.temp.BOT', new_callable=MagicMock)
    async def test_send_update_movie(self, mock_bot, mock_get_status, mock_get_poster):
        # Setup mocks
        mock_get_status.return_value = True

        mock_get_poster.return_value = {
            "title": "Chinna Chinna Aasai",
            "tmdb_id": 10101,
            "kind": "movie",
            "languages": "Malayalam, Tamil",
            "release_date": "2026-06-19",
            "year": "2026",
            "genres": "Drama",
            "rating": None, # Rating is N/A
            "votes": None,
            "poster": "http://example.com/poster.jpg",
            "url": "https://www.themoviedb.org/movie/10101"
        }

        mock_send_photo = AsyncMock()
        mock_bot.send_photo = mock_send_photo
        mock_bot.send_sticker = AsyncMock()

        # Call send_update
        with patch('utils.UPDATES_SEND_CHANNEL', 123456):
            await send_update("Chinna Chinna Aasai", "2026")

        # Check send_photo was called
        mock_send_photo.assert_called_once()
        args, kwargs = mock_send_photo.call_args
        caption = kwargs.get('caption', '')

        # Assert format matches expected Movie format
        self.assertIn("✨ NEW UPLOAD ADDED ✨", caption)
        self.assertIn("🎬 <b><a href='https://www.themoviedb.org/movie/10101'>Chinna Chinna Aasai (2026)</a></b>", caption)
        self.assertIn("🏷️ Category: #Movie", caption)
        self.assertIn("⭐ Rating: N/A", caption)
        self.assertIn("🎭 Genres: #Drama", caption)
        self.assertIn("🌐 Language: #Malayalam, #Tamil", caption)
        self.assertIn("📅 Release: 2026-06-19", caption)

        # Check sticker was sent
        mock_bot.send_sticker.assert_called_once_with(
            chat_id=123456,
            sticker="CAACAgUAAxkBAALIC2poNkeCLO7oGxrvA-J9BuOkQgrdAAK0HgACcVWZVlDepbKeENKoPQQ"
        )

    @patch('utils.get_poster')
    @patch('utils.db.get_movie_update_status', new_callable=AsyncMock)
    @patch('utils.temp.BOT', new_callable=MagicMock)
    @patch('database.ia_filterdb.get_search_results', new_callable=AsyncMock)
    async def test_send_update_tv_single_episode(self, mock_get_results, mock_bot, mock_get_status, mock_get_poster):
        mock_get_status.return_value = True

        mock_get_poster.return_value = {
            "title": "See You at Work Tomorrow!",
            "tmdb_id": 20202,
            "kind": "tv",
            "languages": "Korean",
            "release_date": "2026-06-22",
            "year": "2026",
            "genres": "Comedy, Drama",
            "rating": 9.0,
            "votes": 36,
            "poster": "http://example.com/tv_poster.jpg",
            "url": "https://www.themoviedb.org/tv/20202"
        }

        # Mocking db search results for single file
        mock_get_results.return_value = [
            {"file_name": "See You at Work Tomorrow! S01E11.mkv"}
        ]

        mock_send_photo = AsyncMock()
        mock_bot.send_photo = mock_send_photo
        mock_bot.send_sticker = AsyncMock()

        with patch('utils.UPDATES_SEND_CHANNEL', 123456):
            await send_update("See You at Work Tomorrow!", "2026")

        mock_send_photo.assert_called_once()
        args, kwargs = mock_send_photo.call_args
        caption = kwargs.get('caption', '')

        # Assert format matches expected TV format for single episode
        self.assertIn("✨ NEW UPLOAD ADDED ✨", caption)
        self.assertIn("📺 <b><a href='https://www.themoviedb.org/tv/20202'>See You at Work Tomorrow!</a></b>", caption)
        self.assertIn("🔸 Season 01", caption)
        self.assertIn("🔹 Episode 11 Added", caption)
        self.assertIn("🏷️ Category: #TV", caption)
        self.assertIn("⭐ Rating: 9/10 (36 votes)", caption)
        self.assertIn("🎭 Genres: #Comedy, #Drama", caption)
        self.assertIn("🌐 Language: #Korean", caption)
        self.assertIn("📅 Release: 2026-06-22", caption)

    @patch('utils.get_poster')
    @patch('utils.db.get_movie_update_status', new_callable=AsyncMock)
    @patch('utils.temp.BOT', new_callable=MagicMock)
    @patch('database.ia_filterdb.get_search_results', new_callable=AsyncMock)
    async def test_send_update_tv_multiple_episodes(self, mock_get_results, mock_bot, mock_get_status, mock_get_poster):
        mock_get_status.return_value = True

        mock_get_poster.return_value = {
            "title": "See You at Work Tomorrow!",
            "tmdb_id": 20202,
            "kind": "tv",
            "languages": "Korean",
            "release_date": "2026-06-22",
            "year": "2026",
            "genres": "Comedy, Drama",
            "rating": 9.0,
            "votes": 36,
            "poster": "http://example.com/tv_poster.jpg",
            "url": "https://www.themoviedb.org/tv/20202"
        }

        # Mocking db search results for multiple files
        mock_get_results.return_value = [
            {"file_name": "See You at Work Tomorrow! S01E01.mkv"},
            {"file_name": "See You at Work Tomorrow! S01E10.mkv"}
        ]

        mock_send_photo = AsyncMock()
        mock_bot.send_photo = mock_send_photo
        mock_bot.send_sticker = AsyncMock()

        with patch('utils.UPDATES_SEND_CHANNEL', 123456):
            await send_update("See You at Work Tomorrow!", "2026")

        mock_send_photo.assert_called_once()
        args, kwargs = mock_send_photo.call_args
        caption = kwargs.get('caption', '')

        # Assert format matches expected TV format for multiple episodes
        self.assertIn("✨ NEW UPLOAD ADDED ✨", caption)
        self.assertIn("📺 <b><a href='https://www.themoviedb.org/tv/20202'>See You at Work Tomorrow!</a></b>", caption)
        self.assertIn("🔸 Season 01", caption)
        self.assertIn("🔹 Episodes 1 to 10 Added", caption)
        self.assertIn("🏷️ Category: #TV", caption)
        self.assertIn("⭐ Rating: 9/10 (36 votes)", caption)
        self.assertIn("🎭 Genres: #Comedy, #Drama", caption)
        self.assertIn("🌐 Language: #Korean", caption)
        self.assertIn("📅 Release: 2026-06-22", caption)

if __name__ == '__main__':
    unittest.main()
