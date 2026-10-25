<div align="center">

# 🚀 Nova Filter Bot

**The most complete Auto Filter Bot for Telegram — built for speed, scale, and simplicity.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![MongoDB](https://img.shields.io/badge/MongoDB-Database-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com)
[![License](https://img.shields.io/badge/License-AGPL%20v3.0-blue?style=for-the-badge)](https://github.com/xHansaka-Anuhas/Nova-Filter-Bot/blob/main/LICENSE)

[![Demo Bot](https://img.shields.io/badge/🤖_Demo_Bot-TestbotAf__bot-2CA5E0?style=for-the-badge&logo=telegram)](https://t.me/TestbotAf_bot)
[![Support Group](https://img.shields.io/badge/💬_Support-Nova__Filter__Official-2CA5E0?style=for-the-badge&logo=telegram)](https://t.me/Nova_Filter_Official)

</div>

---

## 📖 What is Nova Filter Bot?

**Nova Filter Bot** is a high-performance Telegram Auto Filter Bot that indexes files from your channels and delivers them to users through fast inline and auto-filter search. It is designed for channel administrators who want a **self-hosted, fully controllable file distribution system** — no middlemen, no monthly fees, no limits beyond what your own infrastructure allows.

Whether you run a movie archive, a software repository, or a private media library, Nova turns your Telegram channels into a **searchable, user-friendly file delivery service**.

---

## ✨ Features at a Glance

| | Feature | Description |
|---|---|---|
| 🔍 | **Auto Filter Search** | Users type a keyword in the group; the bot replies with matching files instantly. |
| 📑 | **Manual Filter** | Admins can set custom keyword-to-file rules for specific groups. |
| 📡 | **Inline Search** | Search across all indexed files from any chat via inline mode. |
| 🎬 | **IMDb / TMDb Integration** | Automatically fetches posters, ratings, and metadata for movies and TV shows. |
| 🔒 | **Force Subscription** | Require users to join your channels before using the bot. |
| 👑 | **Premium / Access Control** | Grant unlimited or priority access to specific users. |
| 📢 | **Broadcast System** | Send messages to all users, all groups, or pin announcements. |
| 🛠️ | **Admin Dashboard** | Full control over files, users, groups, bans, and settings. |
| 🗂️ | **Multi-Channel Indexing** | Index files from multiple channels into a single searchable database. |
| 🌐 | **Multi-Language Support** | Serve users in multiple languages simultaneously. |
| 🖼️ | **Image to Link** | Upload images to `uguu.se` and get a shareable link directly in Telegram. |
| ⚡ | **Fast & Lightweight** | Built on Kurigram (MTProto) for speed; runs comfortably on a 512 MB VPS. |

---

## 🎮 Commands

### 👤 User Commands

| Command | What it does |
|---|---|
| `/start` | Check if the bot is alive and see the welcome message |
| `/ping` | View the bot's latency |
| `/id` | Get the ID of the current group or channel |
| `/img_2_link` | Upload an image to `uguu.se` and receive a direct link |
| `/settings` | Adjust group-level settings (for admins) |
| `/index_channels` | See how many index channels are configured |
| `/stats` | View bot statistics |

### 🛡️ Admin Commands

| Command | What it does |
|---|---|
| `/index` | Index files from a connected channel |
| `/delete` | Delete files matching a query |
| `/delete_all` | Wipe the entire indexed file database |
| `/broadcast` | Send a message to all bot users |
| `/grp_broadcast` | Send a message to all groups |
| `/pin_broadcast` | Broadcast and pin a message to all users |
| `/pin_grp_broadcast` | Broadcast and pin a message to all groups |
| `/ban_user` / `/unban_user` | Ban or unban a user from the bot |
| `/ban_grp` / `/unban_grp` | Disable or enable the bot in a group |
| `/users` | List all registered users |
| `/chats` | List all connected groups |
| `/invite_link` | Generate an invite link for the current chat |
| `/leave` | Remove the bot from a group |
| `/restart` | Restart the bot process |

---

## ⚙️ Configuration

Nova is configured entirely through environment variables. Copy `.env.example` to `.env` and fill in the required values.

### 🔴 Required Variables

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram Bot API token from [@BotFather](https://telegram.dog/BotFather) |
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org/apps) |
| `API_HASH` | Telegram API Hash from [my.telegram.org](https://my.telegram.org/apps) |
| `ADMINS` | Space-separated list of admin user IDs |
| `FILES_DATABASE_URL` | MongoDB connection string for the **files** database |
| `DATA_DATABASE_URL` | MongoDB connection string for **user/group data** |
| `LOG_CHANNEL` | Channel ID where the bot logs activity (bot must be admin) |
| `BIN_CHANNEL` | Channel ID used for streaming and download features (bot must be admin) |

### 🟡 Optional Variables

| Variable | Description |
|---|---|
| `FORCE_SUB_CHANNELS` | Space-separated IDs of channels users must join |
| `REQUEST_FORCE_SUB_CHANNEL` | Channel ID for request-based force subscription |
| `INDEX_CHANNELS` | Usernames or IDs of channels to index |
| `LANGUAGES` | Space-separated language codes for bot search |
| `TMDB_API_KEY` | TMDb API key for fetching movie/TV metadata |
| `UPDATES_SEND_CHANNEL` | Channel ID for new-content notifications |
| `URL` | Your deployed bot URL or VPS IP address |

> 📄 For the full list of optional variables, see [`info.py`](https://github.com/xHansaka-Anuhas/Nova-Filter-Bot/blob/main/info.py).

---

## 🚢 Deployment

Nova can be deployed in four ways. Choose the one that fits your setup.

### ☁️ One-Click Deploy

<div align="center">

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy)

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&builder=dockerfile&repository=https://github.com/xHansaka-Anuhas/Nova-Filter-Bot)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

</div>

### 🖥️ VPS / Docker

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
sudo apt install docker.io -y

# 3. Verify Docker is installed
docker --version

# 4. Enable Docker on boot
sudo systemctl enable docker
sudo systemctl start docker

# 5. Clone the repository
git clone https://github.com/xHansaka-Anuhas/Nova-Filter-Bot
cd Nova-Filter-Bot

# 6. Build the Docker image
sudo docker build -t auto-filter-bot .

# 7. Run the container
sudo docker run -d -p 80:80 --name Auto-Filter-Bot auto-filter-bot

# 8. Verify it is running
sudo docker ps

# 9. Restart if needed
sudo docker restart Auto-Filter-Bot

# 10. Check logs
sudo docker logs Auto-Filter-Bot
