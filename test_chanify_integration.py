import pytest
from unittest.mock import AsyncMock, MagicMock
from pyrogram.handlers import MessageHandler
from bot import Bot, chanify

@pytest.mark.anyio
async def test_chanify_wrapped_callback():
    bot = Bot()

    called = False
    async def dummy_callback(client, message):
        nonlocal called
        called = True

    handler = MessageHandler(dummy_callback)

    original_show_ad = chanify.show_ad
    mock_show_ad = AsyncMock()
    chanify.show_ad = mock_show_ad

    try:
        bot.add_handler(handler)

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.from_user = MagicMock()

        assert not called
        await handler.callback(mock_client, mock_message)

        assert called
        mock_show_ad.assert_called_once_with(chat_id=12345, user=mock_message.from_user)
    finally:
        chanify.show_ad = original_show_ad
