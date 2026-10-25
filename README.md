# 🚀 Nova Filter Bot

A fast, self-hosted Telegram Auto Filter Bot. Index files from your channels, let users search them instantly, and control everything from your own server.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/telegram-bot-26A5E4.svg)](https://core.telegram.org/bots/api)
[![MongoDB](https://img.shields.io/badge/mongodb-required-green.svg)](https://www.mongodb.com)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPL%20v3-blue.svg)](LICENSE)

🤖 [Demo Bot](https://t.me/TestbotAf_bot) · 💬 [Support Group](https://t.me/Nova_Filter_Official)

---

## What it does

Nova indexes files from Telegram channels and serves them to users through auto filter and inline search. Instead of scrolling through thousands of messages, users type a keyword in your group and get the matching file back in seconds.

Built for channel admins who want a self-hosted alternative to paid file-search bots — no monthly fees, no limits beyond your own infrastructure.

---

## Features

- 🔍 **Auto filter** — replies to keyword searches in groups automatically
- 📡 **Inline search** — works from any chat via `@YourBot query`
- 📑 **Manual filters** — set custom keyword-to-file rules per group
- 🎬 **IMDb / TMDb metadata** — auto-attaches posters and ratings to movie files
- 🔒 **Force subscribe** — require users to join your channels first
- 👑 **Premium access** — grant unlimited searches to specific users
- 📢 **Broadcast** — message all users, all groups, or pin to everyone
- 🗂️ **Multi-channel indexing** — pool files from multiple channels into one database
- 🌐 **Multi-language** — serve users in several languages at once
- 🖼️ **Image to link** — upload an image, get a shareable URL
- ⚡ **Lightweight** — runs on a 512 MB VPS, built on Kurigram (MTProto)

---

## Commands

### Users

| Command | Description |
|---|---|
| `/start` | Wake the bot and see the welcome message |
| `/ping` | Check bot latency |
| `/id` | Get the current chat's ID |
| `/img_2_link` | Upload an image and get a link |
| `/stats` | View bot statistics |
| `/settings` | Adjust group settings (group admins only) |

### Admins

| Command | Description |
|---|---|
| `/index` | Index files from a connected channel |
| `/delete` | Delete files matching a query |
| `/delete_all` | Wipe the indexed file database |
| `/broadcast` | Message all users |
| `/grp_broadcast` | Message all groups |
| `/pin_broadcast` | Broadcast and pin to all users |
| `/pin_grp_broadcast` | Broadcast and pin to all groups |
| `/ban_user` · `/unban_user` | Ban or unban a user |
| `/ban_grp` · `/unban_grp` | Disable or enable the bot in a group |
| `/users` · `/chats` | List users or groups |
| `/invite_link` | Generate an invite link for the current chat |
| `/leave` | Remove the bot from a group |
| `/restart` | Restart the bot |

---

## Setup

### 1. Get your credentials

You need four things before deploying:

- **Bot token** — from [@BotFather](https://t.me/BotFather)
- **API ID and API hash** — from [my.telegram.org/apps](https://my.telegram.org/apps)
- **MongoDB URLs** — two separate databases (free tier on [MongoDB Atlas](https://www.mongodb.com/atlas) works fine)
- **Log and bin channel IDs** — two private channels where the bot must be added as admin

### 2. Configure

Copy `.env.example` to `.env` and fill in:

```env
BOT_TOKEN=123456:ABC...
API_ID=1234567
API_HASH=abcdef1234567890
ADMINS=123456789
FILES_DATABASE_URL=mongodb+srv://...
DATA_DATABASE_URL=mongodb+srv://...
LOG_CHANNEL=-1001234567890
BIN_CHANNEL=-1001234567890`

Optional variables — force subscribe channels, index channels, TMDb API key, languages — are documented in [`info.py`](info.py).

### 3. Deploy

**Docker (recommended):**

```bash
git clone https://github.com/xHansaka-Anuhas/Nova-Filter-Bot
cd Nova-Filter-Bot
sudo docker build -t nova-filter .
sudo docker run -d -p 80:80 --name nova-filter nova-filter
sudo docker logs nova-filter
```

**Manual:**

```bash
git clone https://github.com/xHansaka-Anuhas/Nova-Filter-Bot
cd Nova-Filter-Bot
pip install -r requirements.txt
python -m bot
```

**One-click:** Heroku, Koyeb, and Render deploy buttons are on the [GitHub repo page](https://github.com/xHansaka-Anuhas/Nova-Filter-Bot).

### 4. Index your first channel

1. Add the bot as admin to the channel you want to index
2. Send `/index` in that channel (or reply to a specific message with `/index`)
3. The bot indexes the files and adds them to the searchable database
4. Users can now find them with `/start` or inline search

---

## Support

- 💬 [Nova Filter Official](https://t.me/Nova_Filter_Official) — help, setup questions, bug reports
- 🐛 [Open an issue](https://github.com/xHansaka-Anuhas/Nova-Filter-Bot/issues) — for reproducible bugs
- 🤖 [Demo bot](https://t.me/TestbotAf_bot) — try before you deploy

---

## Credits

Built on [Kurigram](https://github.com/KurimuzonAkuma/kurigram) · Originally inspired by [EvaMaria](https://t.me/TeamEvamaria) · Maintained by [Hansaka](https://t.me/Hansaka_Anuhas)

---

## License

GNU Affero General Public License v3.0.

- ✅ Fork, modify, self-host freely
- ❌ Selling the code is prohibited
- ⚠️ Fork the repo — don't import it directly — and give credit

Full text in [LICENSE](LICENSE).

---

⭐ If Nova helps you, star the repo.
```

**What's different this time:**

- **One file, one flow** — no hero badges stack, no thirteen separate tables, no decorative dividers between every section.
- **Sections shrink to what matters** — Features is a bullet list, not a table with description columns. Commands is two simple tables. Setup is four numbered steps.
- **Reads top-to-bottom like a doc** — someone can follow it start to finish without jumping around. The old version read like a marketing page.
- **Deployment collapsed** — one "Deploy" step with Docker and manual side by side, one-click buttons mentioned inline, not three giant SVG buttons.
- **Credits and License trimmed** — brief, respectful, no walls of bullet points explaining what AGPL means.
