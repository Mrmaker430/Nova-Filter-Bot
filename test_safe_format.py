import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from utils import safe_format, temp
import asyncio

class TestCacheInvalidation(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temp.QUERY_CACHE.clear()

    async def asyncTearDown(self):
        temp.QUERY_CACHE.clear()

    @patch("database.ia_filterdb.collection")
    @patch("database.ia_filterdb.trigger_update_if_new", new_callable=AsyncMock)
    @patch("database.ia_filterdb.unpack_new_file_id", return_value="mock_unpacked_id")
    async def test_save_file_clears_cache(self, mock_unpack, mock_trigger, mock_collection):
        mock_collection.insert_one = AsyncMock()

        temp.QUERY_CACHE["test_query"] = ["file1", "file2"]
        self.assertEqual(len(temp.QUERY_CACHE), 1)

        media = MagicMock()
        media.file_id = "mock_file_id"
        media.file_name = "Mock Movie 2024"
        media.caption = "Mock Caption"
        media.file_size = 12345

        from database.ia_filterdb import save_file
        res = await save_file(media)

        self.assertEqual(res, "suc")
        self.assertEqual(len(temp.QUERY_CACHE), 0)

    @patch("database.ia_filterdb.collection")
    async def test_delete_files_clears_cache(self, mock_collection):
        mock_delete_result = MagicMock()
        mock_delete_result.deleted_count = 5
        mock_collection.delete_many = AsyncMock(return_value=mock_delete_result)

        temp.QUERY_CACHE["test_query"] = ["file1", "file2"]
        self.assertEqual(len(temp.QUERY_CACHE), 1)

        from database.ia_filterdb import delete_files
        deleted = await delete_files("Mock Movie")

        self.assertEqual(deleted, 5)
        self.assertEqual(len(temp.QUERY_CACHE), 0)


class TestSafeFormat(unittest.TestCase):
    def test_safe_format_basic(self):
        template = "Hello {name}!"
        result = safe_format(template, name="Alice")
        self.assertEqual(result, "Hello Alice!")

    def test_safe_format_missing_keys(self):
        template = "Hello {name}! Your age is {age}."
        result = safe_format(template, name="Alice")
        self.assertEqual(result, "Hello Alice! Your age is {age}.")

    def test_safe_format_extra_keys(self):
        template = "Hello {name}!"
        result = safe_format(template, name="Alice", age=30)
        self.assertEqual(result, "Hello Alice!")

    def test_safe_format_missing_key_with_format_spec(self):
        template = "Rating is {rating:.1f}, missing is {missing:.2f}"
        result = safe_format(template, rating=4.56)
        self.assertEqual(result, "Rating is 4.6, missing is {missing}")

    def test_safe_format_malformed_braces(self):
        template = "Hello {name! Your age is {age}."
        result = safe_format(template, name="Alice", age=30)
        # Malformed template should fall back to returning template
        self.assertEqual(result, template)

    def test_settings_merging_logic(self):
        # Emulate Database.get_settings merging logic
        default_setgs = {
            'template': 'default',
            'tutorial': 't_default',
            'tutorial_name': 'tn_default',
            'links': True
        }
        
        # Scenario 1: Chat exists but has outdated settings document (missing 'tutorial_name')
        chat_db_settings = {
            'template': 'custom',
            'tutorial': 't_custom',
            'links': False
        }
        
        merged = default_setgs.copy()
        merged.update(chat_db_settings)
        
        self.assertEqual(merged['template'], 'custom')
        self.assertEqual(merged['tutorial'], 't_custom')
        self.assertEqual(merged['tutorial_name'], 'tn_default')
        self.assertEqual(merged['links'], False)

if __name__ == "__main__":
    unittest.main()
