import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from pyrogram.errors import ChatAdminRequired, PeerIdInvalid, RPCError

# Ensure environment variables are set before importing plugins
os.environ.setdefault("API_ID", "12345")
os.environ.setdefault("API_HASH", "mock_hash")
os.environ.setdefault("BOT_TOKEN", "mock_token")
os.environ.setdefault("ADMINS", "12345")
os.environ.setdefault("FILES_DATABASE_URL", "mongodb://localhost:27017")
os.environ.setdefault("DATA_DATABASE_URL", "mongodb://localhost:27017")
os.environ.setdefault("LOG_CHANNEL", "-1001")
os.environ.setdefault("BIN_CHANNEL", "-1002")
os.environ.setdefault("URL", "http://localhost")

from plugins.p_ttishow import gen_invite_link


@pytest.mark.asyncio
async def test_gen_invite_link_no_args():
    bot = AsyncMock()
    message = AsyncMock()
    message.command = ["fetch"]

    await gen_invite_link(bot, message)

    message.reply.assert_called_once()
    assert "Please provide a chat ID or username" in message.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_gen_invite_link_invalid_format():
    bot = AsyncMock()
    message = AsyncMock()
    message.command = ["fetch", "invalid_chat_id"]

    await gen_invite_link(bot, message)

    message.reply.assert_called_once()
    assert "Invalid chat ID format" in message.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_gen_invite_link_numeric_success():
    bot = AsyncMock()
    mock_link = MagicMock()
    mock_link.invite_link = "https://t.me/+AbCdEfGhIjK"
    bot.create_chat_invite_link = AsyncMock(return_value=mock_link)

    message = AsyncMock()
    message.command = ["fetch", "-1001234567890"]

    await gen_invite_link(bot, message)

    bot.create_chat_invite_link.assert_called_once_with(
        chat_id=-1001234567890,
        name="Bot-generated link"
    )
    message.reply.assert_called_once()
    reply_text = message.reply.call_args[0][0]
    assert "Invite link generated successfully!" in reply_text
    assert "-1001234567890" in reply_text
    assert "https://t.me/+AbCdEfGhIjK" in reply_text


@pytest.mark.asyncio
async def test_gen_invite_link_username_success():
    bot = AsyncMock()
    mock_link = MagicMock()
    mock_link.invite_link = "https://t.me/+ZzYyXxWwVv"
    bot.create_chat_invite_link = AsyncMock(return_value=mock_link)

    message = AsyncMock()
    message.command = ["invite_link", "@mygroup"]

    await gen_invite_link(bot, message)

    bot.create_chat_invite_link.assert_called_once_with(
        chat_id="@mygroup",
        name="Bot-generated link"
    )
    message.reply.assert_called_once()
    reply_text = message.reply.call_args[0][0]
    assert "Invite link generated successfully!" in reply_text
    assert "@mygroup" in reply_text
    assert "https://t.me/+ZzYyXxWwVv" in reply_text


@pytest.mark.asyncio
async def test_gen_invite_link_chat_admin_required():
    bot = AsyncMock()
    bot.create_chat_invite_link = AsyncMock(side_effect=ChatAdminRequired())

    message = AsyncMock()
    message.command = ["fetch", "-1001234567890"]

    await gen_invite_link(bot, message)

    message.reply.assert_called_once()
    reply_text = message.reply.call_args[0][0]
    assert "Permission denied." in reply_text
    assert "administrator" in reply_text


@pytest.mark.asyncio
async def test_gen_invite_link_peer_id_invalid():
    bot = AsyncMock()
    bot.create_chat_invite_link = AsyncMock(side_effect=PeerIdInvalid())

    message = AsyncMock()
    message.command = ["fetch", "-1001234567890"]

    await gen_invite_link(bot, message)

    message.reply.assert_called_once()
    reply_text = message.reply.call_args[0][0]
    assert "Could not generate invite link." in reply_text
    assert "Please ensure:" in reply_text


@pytest.mark.asyncio
async def test_gen_invite_link_rpc_error():
    bot = AsyncMock()
    bot.create_chat_invite_link = AsyncMock(side_effect=RPCError())

    message = AsyncMock()
    message.command = ["fetch", "-1001234567890"]

    await gen_invite_link(bot, message)

    message.reply.assert_called_once()
    reply_text = message.reply.call_args[0][0]
    assert "Telegram error occurred." in reply_text
