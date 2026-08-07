import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from bot import Bot
from pyrogram import types, StopPropagation

class TestBotListener(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_listeners_does_not_clear_new_listener(self):
        # Create bot instance (mocking Client.__init__ and add_handler)
        with patch('pyrogram.Client.__init__', return_value=None), \
             patch('pyrogram.Client.add_handler', return_value=None):
            bot = Bot()
            bot.listeners = {}

            chat_id = 98765
            user_id = 12345
            listener_id = (chat_id, user_id)

            # Task 1 starts listening
            task1 = asyncio.create_task(bot.listen(chat_id, user_id, timeout=2))

            # Allow task1 to register itself in bot.listeners
            await asyncio.sleep(0.1)
            self.assertIn(listener_id, bot.listeners)
            future1 = bot.listeners[listener_id]

            # Task 2 starts listening (concurrency)
            task2 = asyncio.create_task(bot.listen(chat_id, user_id, timeout=2))

            # Allow task2 to execute and cancel task1, and register itself
            await asyncio.sleep(0.1)
            self.assertIn(listener_id, bot.listeners)
            future2 = bot.listeners[listener_id]

            # Verify future1 is cancelled/different and future2 is active
            self.assertIsNot(future1, future2)
            self.assertTrue(future1.done())
            self.assertFalse(future2.done())

            # Now, simulate a message being sent to task2.
            mock_message = MagicMock()
            mock_message.chat = MagicMock()
            mock_message.chat.id = chat_id
            mock_message.from_user = MagicMock()
            mock_message.from_user.id = user_id

            # Trigger the handler on task2
            with self.assertRaises(StopPropagation):
                await bot._listener_handler(None, mock_message)

            # task2 should return the message now
            result = await task2
            self.assertEqual(result, mock_message)

            # And since task2 completed successfully, listener_id should be cleaned up
            self.assertNotIn(listener_id, bot.listeners)

            # Ensure task1 completed by raising a CancelledError
            with self.assertRaises(asyncio.CancelledError):
                await task1

    async def test_listener_handler_stops_propagation_only_when_not_done(self):
        with patch('pyrogram.Client.__init__', return_value=None), \
             patch('pyrogram.Client.add_handler', return_value=None):
            bot = Bot()
            bot.listeners = {}

            chat_id = 98765
            user_id = 12345
            listener_id = (chat_id, user_id)

            # Create a future and set it in bot.listeners, then complete/cancel it
            future = asyncio.get_event_loop().create_future()
            bot.listeners[listener_id] = future
            future.cancel() # Make it done

            mock_message = MagicMock()
            mock_message.chat = MagicMock()
            mock_message.chat.id = chat_id
            mock_message.from_user = MagicMock()
            mock_message.from_user.id = user_id

            # Since the future is already done, calling _listener_handler should NOT raise StopPropagation
            # This ensures standard handlers can process it.
            try:
                await bot._listener_handler(None, mock_message)
            except StopPropagation:
                self.fail("_listener_handler raised StopPropagation on a done future!")

if __name__ == "__main__":
    unittest.main()
