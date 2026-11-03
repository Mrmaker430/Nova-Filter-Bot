import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

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

from database.users_chats_db import db
from database.ia_filterdb import remove_bad_words_from_db, save_file
from plugins.pm_filter import pm_search


class TestBadWordsAndPMSearch(unittest.TestCase):

    def test_pm_search_status_db(self):
        async def run_test():
            with patch.object(db.stg, 'find_one', new=AsyncMock(return_value={'PM_SEARCH': False})):
                status = await db.get_pm_search_status()
                self.assertFalse(status)

            with patch.object(db.stg, 'update_one', new=AsyncMock()) as mock_update:
                await db.set_pm_search_status(True)
                mock_update.assert_called_once()

        asyncio.run(run_test())

    def test_bad_words_db_methods(self):
        async def run_test():
            with patch.object(db.stg, 'find_one', new=AsyncMock(return_value={'BAD_WORDS': ['junk', 'test']})):
                words = await db.get_bad_words()
                self.assertEqual(words, ['junk', 'test'])

            with patch.object(db.stg, 'find_one', new=AsyncMock(return_value={'BAD_WORDS': ['junk']})), \
                 patch.object(db.stg, 'update_one', new=AsyncMock()) as mock_update:
                res = await db.add_bad_words(['bad', 'spam'])
                self.assertIn('junk', res)
                self.assertIn('bad', res)
                self.assertIn('spam', res)
                mock_update.assert_called_once()

            with patch.object(db.stg, 'find_one', new=AsyncMock(return_value={'BAD_WORDS': ['junk', 'bad']})), \
                 patch.object(db.stg, 'update_one', new=AsyncMock()) as mock_update:
                res = await db.remove_bad_words(['junk'])
                self.assertNotIn('junk', res)
                self.assertIn('bad', res)
                mock_update.assert_called_once()

        asyncio.run(run_test())

    @patch('database.ia_filterdb.second_collection')
    @patch('database.ia_filterdb.collection')
    def test_remove_bad_words_from_db(self, mock_collection, mock_second_collection):
        async def run_test():
            doc1 = {'_id': 'f1', 'file_name': 'Inception 2010 mdisk hdrip.mkv'}
            doc2 = {'_id': 'f2', 'file_name': 'Interstellar 2014 mdisk.mkv'}

            # Mock cursor for primary collection
            async def async_iter1():
                yield doc1

            cursor1 = MagicMock()
            cursor1.__aiter__ = lambda s: async_iter1()
            mock_collection.find.return_value = cursor1
            mock_collection.update_one = AsyncMock()

            # Mock cursor for second collection
            async def async_iter2():
                yield doc2

            cursor2 = MagicMock()
            cursor2.__aiter__ = lambda s: async_iter2()
            mock_second_collection.find.return_value = cursor2
            mock_second_collection.update_one = AsyncMock()

            updated = await remove_bad_words_from_db(['mdisk'])
            self.assertEqual(updated, 2)
            mock_collection.update_one.assert_called_once_with({'_id': 'f1'}, {'$set': {'file_name': 'Inception 2010 hdrip.mkv'}})
            mock_second_collection.update_one.assert_called_once_with({'_id': 'f2'}, {'$set': {'file_name': 'Interstellar 2014.mkv'}})

        asyncio.run(run_test())

    @patch('database.ia_filterdb.unpack_new_file_id', return_value='file_id_123')
    @patch('database.ia_filterdb.second_collection')
    @patch('database.ia_filterdb.collection')
    def test_save_file_strips_bad_words(self, mock_collection, mock_second_collection, mock_unpack):
        async def run_test():
            mock_media = MagicMock()
            mock_media.file_id = 'media_id'
            mock_media.file_name = 'Avatar.2009.mdisk.spam.1080p.mkv'
            mock_media.file_size = 5000
            mock_media.caption = 'Avatar caption'

            mock_second_collection.find_one = AsyncMock(return_value=None)
            mock_collection.insert_one = AsyncMock(return_value=MagicMock())

            with patch('database.users_chats_db.db.get_bad_words', new=AsyncMock(return_value=['mdisk', 'spam'])), \
                 patch('database.ia_filterdb.trigger_update_if_new', new=AsyncMock()):
                result = await save_file(mock_media)
                self.assertEqual(result, 'suc')
                saved_doc = mock_collection.insert_one.call_args[0][0]
                self.assertEqual(saved_doc['file_name'], 'Avatar 2009 1080p mkv')

        asyncio.run(run_test())

    def test_pm_search_disabled_response(self):
        async def run_test():
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.text = "Inception"
            mock_message.from_user.mention = "John"
            mock_message.reply_text = AsyncMock()

            with patch('database.users_chats_db.db.get_pm_search_status', new=AsyncMock(return_value=False)):
                await pm_search(mock_client, mock_message)
                mock_message.reply_text.assert_called_once()
                args, kwargs = mock_message.reply_text.call_args
                reply_text = args[0]
                self.assertIn("🙋 ʜᴇʏ  John😍", reply_text)
                self.assertIn("ʏᴏᴜ ᴄᴀɴ sᴇᴀʀᴄʜ 🕵️ ʏᴏᴜʀ ғᴀᴠᴏʀɪᴛᴇ ᴍᴏᴠɪᴇs/sᴇʀɪᴇs ⚝ ᴋɪɴᴅʟʏ ʀᴇǫᴜᴇsᴛ ɪɴ ʀᴇqᴜᴇꜱᴛ ɢʀᴏᴜᴘ", reply_text)
                self.assertIn("আপনি আপনার প্রিয় মুভি/সিরিজ খুঁজতে পারেন ⚝ রিকোয়েস্ট গ্রুপ এ রিকোয়েস্ট করুন।", reply_text)
                markup = kwargs['reply_markup']
                button = markup.inline_keyboard[0][0]
                self.assertEqual(button.text, '💬 ʀᴇǫᴜᴇsᴛ ɢʀᴏᴜᴘ')

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
