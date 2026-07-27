import unittest
from io import BytesIO
from unittest.mock import patch, MagicMock
from poster_generator import generate_movie_poster

class TestPosterGenerator(unittest.IsolatedAsyncioTestCase):
    @patch('poster_generator.requests.get')
    async def test_generate_movie_poster_mock_success(self, mock_get):
        # Setup mock responses for backdrop and poster images
        from PIL import Image

        # Create small dummy images for mock downloads
        img_io = BytesIO()
        Image.new('RGB', (100, 100), color='blue').save(img_io, 'JPEG')
        img_bytes = img_io.getvalue()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = img_bytes
        mock_get.return_value = mock_resp

        # Create dummy movie data
        movie_data = {
            "title": "Alice in Borderland",
            "tmdb_id": 91919,
            "kind": "tv",
            "languages": "Japanese, English",
            "countries": "Japan",
            "release_date": "2020-12-10",
            "year": "2020",
            "genres": "Mystery, Drama, Sci-Fi",
            "runtime": None,
            "rating": 8.123,
            "votes": 1200,
            "poster": "https://image.tmdb.org/t/p/original/mock_poster.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/mock_backdrop.jpg",
            "seasons": 3,
            "plot": "With his two friends, a video-game-obsessed young man finds himself in a strange version of Tokyo where they must compete in dangerous games to win."
        }

        # Run poster generation
        poster_io = None
        try:
            poster_io = await generate_movie_poster(movie_data)
        except Exception as e:
            self.fail(f"generate_movie_poster raised an exception: {e}")

        self.assertIsNotNone(poster_io)
        self.assertEqual(poster_io.name, "poster.png")

        # Verify it can be loaded as an Image
        from PIL import Image as PILImage
        img = PILImage.open(poster_io)
        self.assertEqual(img.size, (1280, 720))

    @patch('poster_generator.requests.get')
    async def test_generate_movie_poster_fallback_on_network_failure(self, mock_get):
        # Network call fails or returns 404
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        movie_data = {
            "title": "Alice in Borderland",
            "tmdb_id": 91919,
            "kind": "tv",
            "languages": "Japanese, English",
            "countries": "Japan",
            "release_date": "2020-12-10",
            "year": "2020",
            "genres": "Mystery, Drama, Sci-Fi",
            "runtime": None,
            "rating": 8.123,
            "votes": 1200,
            "poster": "https://image.tmdb.org/t/p/original/mock_poster.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/mock_backdrop.jpg",
            "seasons": 3,
            "plot": "With his two friends, a video-game-obsessed young man finds himself in a strange version of Tokyo where they must compete in dangerous games to win."
        }

        # Run poster generation
        poster_io = await generate_movie_poster(movie_data)

        self.assertIsNotNone(poster_io)
        from PIL import Image as PILImage
        img = PILImage.open(poster_io)
        self.assertEqual(img.size, (1280, 720))

def generate_local_sample():
    # Helper to generate a local sample image file for manual inspection
    import asyncio
    movie_data = {
        "title": "Alice in Borderland",
        "tmdb_id": 91919,
        "kind": "tv",
        "languages": "Japanese, English",
        "countries": "Japan",
        "release_date": "2020-12-10",
        "year": "2020",
        "genres": "Mystery, Drama, Sci-Fi",
        "runtime": None,
        "rating": 8.1,
        "votes": 1200,
        "poster": "https://image.tmdb.org/t/p/original/v79vA790938uS7066Cvsx5TMvHG.jpg",
        "backdrop": "https://image.tmdb.org/t/p/original/9i7LaS96Y8Oq049U696v2N8669q.jpg",
        "seasons": 3,
        "plot": "With his two friends, a video-game-obsessed young man finds himself in a strange version of Tokyo where they must compete in dangerous games to win."
    }
    try:
        print("Generating a test sample poster using real backdrop and poster image URLs...")
        poster_io = asyncio.run(generate_movie_poster(movie_data))
        with open("test_poster_output.jpg", "wb") as f:
            f.write(poster_io.getvalue())
        print("Success! Generated poster saved as 'test_poster_output.jpg'.")
    except Exception as e:
        print(f"Error generating local sample: {e}")

if __name__ == "__main__":
    import sys
    if "--sample" in sys.argv:
        generate_local_sample()
    else:
        unittest.main()
