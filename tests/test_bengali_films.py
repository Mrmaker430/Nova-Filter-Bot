import os
import unittest
from unittest.mock import AsyncMock, patch

# Set mock env vars before importing info or utils
os.environ.setdefault('API_ID', '12345')
os.environ.setdefault('API_HASH', 'abcdef1234567890abcdef1234567890')
os.environ.setdefault('BOT_TOKEN', '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11')
os.environ.setdefault('ADMINS', '12345678')
os.environ.setdefault('FILES_DATABASE_URL', 'mongodb://localhost:27017/files_db')
os.environ.setdefault('DATA_DATABASE_URL', 'mongodb://localhost:27017/data_db')
os.environ.setdefault('LOG_CHANNEL', '-1001234567890')
os.environ.setdefault('BIN_CHANNEL', '-1001234567890')
os.environ.setdefault('URL', 'https://example.com/')

from utils import query_wikidata, get_image_url_from_commons, search_bengali_films_wikidata, get_poster


class TestBengaliFilms(unittest.IsolatedAsyncioTestCase):

    async def test_query_wikidata_success(self):
        fake_response = {
            "results": {
                "bindings": [
                    {
                        "film": {"value": "http://www.wikidata.org/entity/Q16345351"},
                        "filmLabel": {"value": "Game"},
                        "year": {"value": "2014"},
                        "imdbId": {"value": "tt4418120"},
                        "image": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Game_poster.jpg"}
                    }
                ]
            }
        }
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=fake_response)
            mock_get.return_value.__aenter__.return_value = mock_resp

            result = await query_wikidata("SELECT * WHERE { ... }")
            self.assertEqual(result, fake_response)

    async def test_query_wikidata_failure(self):
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.status = 500
            mock_get.return_value.__aenter__.return_value = mock_resp

            result = await query_wikidata("SELECT * WHERE { ... }")
            self.assertIsNone(result)

    async def test_get_image_url_from_commons(self):
        fake_commons_resp = {
            "query": {
                "pages": {
                    "12345": {
                        "imageinfo": [
                            {
                                "thumburl": "https://thumb.wikimedia.org/wikipedia/commons/thumb/game.jpg",
                                "url": "https://upload.wikimedia.org/wikipedia/commons/game.jpg"
                            }
                        ]
                    }
                }
            }
        }
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=fake_commons_resp)
            mock_get.return_value.__aenter__.return_value = mock_resp

            url = await get_image_url_from_commons("http://commons.wikimedia.org/wiki/Special:FilePath/Game_poster.jpg")
            self.assertEqual(url, "https://thumb.wikimedia.org/wikipedia/commons/thumb/game.jpg")

    async def test_get_image_url_from_commons_empty(self):
        url = await get_image_url_from_commons("")
        self.assertIsNone(url)

    async def test_search_bengali_films_wikidata(self):
        fake_wikidata_resp = {
            "results": {
                "bindings": [
                    {
                        "film": {"value": "http://www.wikidata.org/entity/Q16345351"},
                        "filmLabel": {"value": "Game"},
                        "year": {"value": "2014"},
                        "imdbId": {"value": "tt4418120"},
                        "image": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Game_poster.jpg"}
                    },
                    {
                        "film": {"value": "http://www.wikidata.org/entity/Q99999999"},
                        "filmLabel": {"value": "Another Film"},
                        "year": {"value": "2020"},
                        "imdbId": {"value": "tt9999999"},
                        "image": None
                    }
                ]
            }
        }
        with patch("utils.query_wikidata", new=AsyncMock(return_value=fake_wikidata_resp)), \
             patch("utils.get_image_url_from_commons", new=AsyncMock(return_value="https://thumb.wikimedia.org/thumb.jpg")):

            # Filter matching Game
            films = await search_bengali_films_wikidata(title_filter="Game", year=2014)
            self.assertEqual(len(films), 1)
            self.assertEqual(films[0]["title"], "Game")
            self.assertEqual(films[0]["year"], "2014")
            self.assertEqual(films[0]["imdb_id"], "tt4418120")
            self.assertEqual(films[0]["poster_url"], "https://thumb.wikimedia.org/thumb.jpg")

    async def test_get_poster_fallback_to_bengali_wikidata(self):
        # Case when TMDB returns nothing, but Wikidata has the Bengali film
        fake_bengali_movie = [{
            "title": "Chander Pahar",
            "year": "2013",
            "imdb_id": "tt3398018",
            "wikidata_url": "http://www.wikidata.org/entity/Q15296469",
            "poster_url": "https://thumb.wikimedia.org/chander_pahar.jpg"
        }]

        with patch("aiohttp.ClientSession.get") as mock_get, \
             patch("utils.search_bengali_films_wikidata", new=AsyncMock(return_value=fake_bengali_movie)):

            # Mock TMDB returning 0 results
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value={"results": []})
            mock_get.return_value.__aenter__.return_value = mock_resp

            poster_data = await get_poster("Chander Pahar 2013")
            self.assertIsNotNone(poster_data)
            self.assertEqual(poster_data["title"], "Chander Pahar")
            self.assertEqual(poster_data["year"], "2013")
            self.assertEqual(poster_data["languages"], "#Bengali")
            self.assertEqual(poster_data["countries"], "#India")
            self.assertEqual(poster_data["poster"], "https://thumb.wikimedia.org/chander_pahar.jpg")
            self.assertEqual(poster_data["url"], "https://www.imdb.com/title/tt3398018")


if __name__ == "__main__":
    unittest.main()
