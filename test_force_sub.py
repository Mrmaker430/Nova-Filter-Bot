import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from pyrogram import enums
from pyrogram.errors import UserNotParticipant
import asyncio

class TestForceSubscription(unittest.IsolatedAsyncioTestCase):
    @patch("utils.is_premium", new_callable=AsyncMock)
    @patch("utils.db", new_callable=AsyncMock)
    @patch("utils.FORCE_SUB_CHANNELS", "12345")
    @patch("utils.REQUEST_FORCE_SUB_CHANNEL", "")
    async def test_is_subscribed_member_status_active(self, mock_db, mock_is_premium):
        mock_is_premium.return_value = False
        bot = AsyncMock()
        query = MagicMock()
        query.from_user.id = 11111

        chat = MagicMock()
        chat.title = "Test Channel"
        chat.invite_link = "https://t.me/test"
        bot.get_chat.return_value = chat

        member = MagicMock()
        member.status = enums.ChatMemberStatus.MEMBER
        bot.get_chat_member.return_value = member

        from utils import is_subscribed
        btn = await is_subscribed(bot, query)
        self.assertEqual(len(btn), 0)

    @patch("utils.is_premium", new_callable=AsyncMock)
    @patch("utils.db", new_callable=AsyncMock)
    @patch("utils.FORCE_SUB_CHANNELS", "12345")
    @patch("utils.REQUEST_FORCE_SUB_CHANNEL", "")
    async def test_is_subscribed_member_status_left(self, mock_db, mock_is_premium):
        mock_is_premium.return_value = False
        bot = AsyncMock()
        query = MagicMock()
        query.from_user.id = 11111

        chat = MagicMock()
        chat.title = "Test Channel"
        chat.invite_link = "https://t.me/test"
        bot.get_chat.return_value = chat

        member = MagicMock()
        member.status = enums.ChatMemberStatus.LEFT
        bot.get_chat_member.return_value = member

        from utils import is_subscribed
        btn = await is_subscribed(bot, query)
        self.assertEqual(len(btn), 1)
        self.assertEqual(btn[0][0].text, "📢 Join : Test Channel")

    @patch("utils.is_premium", new_callable=AsyncMock)
    @patch("utils.db", new_callable=AsyncMock)
    @patch("utils.FORCE_SUB_CHANNELS", "12345")
    @patch("utils.REQUEST_FORCE_SUB_CHANNEL", "")
    async def test_is_subscribed_user_not_participant_exception(self, mock_db, mock_is_premium):
        mock_is_premium.return_value = False
        bot = AsyncMock()
        query = MagicMock()
        query.from_user.id = 11111

        chat = MagicMock()
        chat.title = "Test Channel"
        chat.invite_link = "https://t.me/test"
        bot.get_chat.return_value = chat

        bot.get_chat_member.side_effect = UserNotParticipant

        from utils import is_subscribed
        btn = await is_subscribed(bot, query)
        self.assertEqual(len(btn), 1)
        self.assertEqual(btn[0][0].text, "📢 Join : Test Channel")

    @patch("database.users_chats_db.data_db")
    async def test_db_remove_join_req(self, mock_data_db):
        from database.users_chats_db import Database
        # Mock database initialization
        mock_data_db.Requests = MagicMock()
        mock_data_db.Requests.delete_one = AsyncMock()

        db_instance = Database()
        await db_instance.remove_join_req(12345)

        mock_data_db.Requests.delete_one.assert_called_once_with({'id': 12345})


if __name__ == "__main__":
    unittest.main()
