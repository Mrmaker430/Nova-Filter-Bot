import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pymongo.errors import OperationFailure, PyMongoError, DuplicateKeyError

# Set mock env vars before importing info or database modules
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

class TestIAFilterDB(unittest.TestCase):

    @patch('database.ia_filterdb.unpack_new_file_id', return_value='test_file_id_1')
    @patch('database.ia_filterdb.second_collection')
    @patch('database.ia_filterdb.collection')
    @patch('database.ia_filterdb.SECOND_FILES_DATABASE_URL', 'mongodb://localhost:27017/second_files_db')
    def test_save_file_duplicate_in_second_db(self, mock_collection, mock_second_collection, mock_unpack):
        from database.ia_filterdb import save_file

        mock_media = MagicMock()
        mock_media.file_id = 'media_id_1'
        mock_media.file_name = 'Test.Movie.2024.mp4'
        mock_media.file_size = 1000000
        mock_media.caption = 'Test Caption'

        # Simulate file already exists in second collection
        mock_second_collection.find_one = AsyncMock(return_value={'_id': 'test_file_id_1'})

        result = asyncio.run(save_file(mock_media))
        self.assertEqual(result, 'dup')
        mock_collection.insert_one.assert_not_called()

    @patch('database.ia_filterdb.unpack_new_file_id', return_value='test_file_id_2')
    @patch('database.ia_filterdb.second_collection')
    @patch('database.ia_filterdb.collection')
    @patch('database.ia_filterdb.SECOND_FILES_DATABASE_URL', 'mongodb://localhost:27017/second_files_db')
    def test_save_file_failover_to_second_db(self, mock_collection, mock_second_collection, mock_unpack):
        from database.ia_filterdb import save_file

        mock_media = MagicMock()
        mock_media.file_id = 'media_id_2'
        mock_media.file_name = 'Test.Movie.2024.mp4'
        mock_media.file_size = 1000000
        mock_media.caption = 'Test Caption'

        # File not in second db
        mock_second_collection.find_one = AsyncMock(return_value=None)
        # Primary db insert fails with quota error/OperationFailure
        mock_collection.insert_one = AsyncMock(side_effect=OperationFailure('quota exceeded'))
        # Second db insert succeeds
        mock_second_collection.insert_one = AsyncMock(return_value=MagicMock())

        with patch('database.ia_filterdb.trigger_update_if_new', new=AsyncMock()):
            result = asyncio.run(save_file(mock_media))
        self.assertEqual(result, 'suc')
        mock_second_collection.insert_one.assert_called_once()

    @patch('database.ia_filterdb.second_collection')
    @patch('database.ia_filterdb.collection')
    @patch('database.ia_filterdb.SECOND_FILES_DATABASE_URL', 'mongodb://localhost:27017/second_files_db')
    def test_get_search_results_deduplication(self, mock_collection, mock_second_collection):
        from database.ia_filterdb import get_search_results

        doc_common = {'_id': 'file_1', 'file_name': 'Inception 2010 1080p.mkv', 'file_size': 2000000}
        doc_unique_2 = {'_id': 'file_2', 'file_name': 'Inception 2010 720p.mkv', 'file_size': 1000000}

        cursor1 = MagicMock()
        cursor1.to_list = AsyncMock(return_value=[doc_common])
        mock_collection.find.return_value = cursor1

        cursor2 = MagicMock()
        cursor2.to_list = AsyncMock(return_value=[doc_common, doc_unique_2])
        mock_second_collection.find.return_value = cursor2

        results = asyncio.run(get_search_results('Inception'))

        # Result should contain 2 unique files, not 3 (doc_common should be deduplicated)
        self.assertEqual(len(results), 2)
        ids = [r['_id'] for r in results]
        self.assertEqual(ids, ['file_1', 'file_2'])

if __name__ == '__main__':
    unittest.main()
