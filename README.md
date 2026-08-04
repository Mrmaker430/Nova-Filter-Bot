<div align="center">

# 🤖 Nova Filter Bot 🤖

</div>

## 𝐹𝑒𝑎𝑡𝑢𝑟𝑒𝑠
- [x] 𝐼𝑀𝐷𝐵 𝑇𝑒𝑚𝑝𝑙𝑎𝑡𝑒 𝑆𝑒𝑡
- [x] 𝑂𝑛𝑙𝑖𝑛𝑒 𝑠𝑡𝑟𝑒𝑎𝑚 𝑎𝑛𝑑 𝑑𝑜𝑤𝑛𝑙𝑜𝑎𝑑
- [x] 𝑉𝑒𝑟𝑖𝑓𝑖𝑐𝑎𝑡𝑖𝑜𝑛 𝑚𝑒𝑡ℎ𝑜𝑑
- [x] 𝐹𝑖𝑙𝑒 𝑐𝑎𝑝𝑡𝑖𝑜𝑛 𝑠𝑒𝑡
- [x] 𝐼𝑛𝑑𝑒𝑥𝑒𝑠 𝐹𝑖𝑙𝑒𝑠 𝑎𝑏𝑜𝑣𝑒 4𝐺𝐵
- [x] 𝑆𝑝𝑒𝑐𝑖𝑓𝑖𝑐 𝑓𝑖𝑙𝑒𝑠 𝐷𝑒𝑙𝑒𝑡𝑒 𝑀𝑜𝑑𝑒
- [x] 𝑆𝑒𝑡𝑡𝑖𝑛𝑔𝑠 𝑀𝑒𝑛𝑢
- [x] 𝑀𝑢𝑙𝑡𝑖𝑝𝑙𝑒 𝐹𝑜𝑟𝑐𝑒 𝑆𝑢𝑏𝑠𝑐𝑟𝑖𝑝𝑡𝑖𝑜𝑛
- [x] 𝑊𝑒𝑙𝑐𝑜𝑚𝑒 𝑀𝑒𝑠𝑠𝑎𝑔𝑒 𝑆𝑒𝑡
- [x] 𝑆ℎ𝑜𝑟𝑡𝑙𝑖𝑛𝑘 𝑠𝑢𝑝𝑝𝑜𝑟𝑡
- [x] 𝐴𝑢𝑡𝑜𝑚𝑎𝑡𝑖𝑐 𝐹𝑖𝑙𝑒 𝐹𝑖𝑙𝑡𝑒𝑟𝑖𝑛𝑔
- [x] 𝐹𝑖𝑙𝑒 𝑃𝑟𝑜𝑡𝑒𝑐𝑡
- [x] 𝑈𝑠𝑒𝑟 𝐵𝑟𝑜𝑎𝑑𝑐𝑎𝑠𝑡
- [x] 𝐺𝑟𝑜𝑢𝑝 𝐵𝑟𝑜𝑎𝑑𝑐𝑎𝑠𝑡
- [x] 𝐼𝑛𝑙𝑖𝑛𝑒 𝑆𝑒𝑎𝑟𝑐ℎ
- [x] 𝑅𝑎𝑛𝑑𝑜𝑚 𝑝𝑖𝑐𝑠
- [x] 𝐵𝑜𝑡 𝑆𝑡𝑎𝑡𝑠
- [x] 𝑆𝑝𝑒𝑙𝑙𝑖𝑛𝑔 𝐶ℎ𝑒𝑐𝑘 𝐹𝑒𝑎𝑡𝑢𝑟𝑒
- [x] 𝐴𝑢𝑡𝑜 𝐷𝑒𝑙𝑒𝑡𝑒
- [x] 𝐴𝑛𝑑 𝑀𝑜𝑟𝑒...

---

### 🆕 Recently Added Advanced Features (Powered by Jules)
We have recently upgraded Nova Filter Bot with a set of robust, enterprise-ready features and optimizations co-developed with **Jules (AI Software Engineer)**:

* 🎨 **Pillow-Based Landscape Banner Generator** (`poster_generator.py`):
  - Automatically renders beautiful, stylized `1280x720` landscape banners for new movie and TV show channel updates.
  - Features real-time poster and backdrop download, custom backdrop blurring, movie poster overlay, high-contrast badges for languages/genres, wrapped plot summaries, and custom Telegram-themed watermarks.
* 🛠️ **Safe Template Formatting** (`safe_format`):
  - Introduced a secure formatting utility for all user-customizable templates (such as dynamic file captions, welcome messages, and custom texts).
  - Prevents application-wide crashes caused by malformed user inputs, missing keyword arguments, or invalid format specifiers by falling back safely to raw text or default strings.
* 📺 **Advanced TV Show Updates Format & Editing**:
  - Automatically formats newly indexed TV shows sent to the updates channel.
  - Formats season and episode details dynamically (e.g., `🔹 Episodes 1 to {max_ep} Added` for multiple episodes, or `🔹 Episode {max_ep} Added` for single ones).
  - Utilizes smart message editing (`edit_message_caption` or `edit_message_text`) to append details to existing update posts rather than flooding the channel with duplicate messages.
* 🔍 **Smart TMDb Search & Poster Cleaning**:
  - Automatically cleans season and episode indicators (e.g., `S01`, `S01E01`, `Season 1`) from the file search title before querying the TMDb API.
  - Ensures faster and exponentially more accurate movie/show metadata matches on TMDb.
* 🛡️ **Strict Live Force Subscription**:
  - Enforces a live subscription check (`is_subscribed`) directly with the Telegram API on every file request.
  - Strictly validates real-time status (including handling users with status `LEFT` or `BANNED`), completely avoiding database caching of membership statuses or premium-bypass issues.
* ⚙️ **Enhanced Startup Validation & DB Stability**:
  - Validates `API_ID` on startup to ensure it is a valid 32-bit signed integer, avoiding cryptic Pyrogram/MTProto serialization overflow crashes (e.g., if a user mistakenly inputs their phone number or bot token).
  - Merges outdated database group documents with `default_setgs` seamlessly, ensuring the bot never crashes when encountering older database schemas.

---

## Demo Bot
* [![Demo](https://img.shields.io/static/v1?label=Demo&message=Bot&color=critical)](https://t.me/TestbotAf_bot)

## 𝐶𝑜𝑚𝑚𝑎𝑛𝑑𝑠
```
• /start - to check bot alive or not.
• /index_channels - to check how many index channel id added.
• /stats - to get bot status.
• /ping - view bot's ping (latency)
• /img_2_link - upload image to uguu.se and get link
• /settings - to change group settings as your wish.
• /delete - to delete files using query.
• /delete_all - to delete all indexed file.
• /broadcast - to send message to all bot users.
• /grp_broadcast - to send message to all groups.
• /pin_broadcast - to send message as pin to all bot users.
• /pin_grp_broadcast - to send message as pin to all groups.
• /restart - to restart bot.
• /id - to check group or channel id.
• /leave - to leave your bot from particular group.
• /unban_grp - to enable group.
• /ban_grp - to disable group.
• /ban_user - to ban a users from bot.
• /unban_user - to unban a users from bot.
• /users - to get all users details.
• /chats - to get all groups.
• /invite_link - to generate invite link.
• /index - to index bot accessible channels.
```

## Variables
### Required Variables
* `BOT_TOKEN`: Create a bot using [@BotFather](https://telegram.dog/BotFather), and get the Telegram API token.
* `API_ID`: Get this value from [telegram.org](https://my.telegram.org/apps)
* `API_HASH`: Get this value from [telegram.org](https://my.telegram.org/apps)
* `ADMINS`: ID of Admins. (Multiple admins can be used separated by space)
* `FILES_DATABASE_URL`: MongoDB URL for 1st files database. Get this value from [MongoDB](https://www.mongodb.com). For more help watch this [video](https://youtu.be/1G1XwEOnxxo)
* `DATA_DATABASE_URL`: for save user, group, etc data.
* `LOG_CHANNEL` : A channel to log the activities of bot. add channel id and Make sure bot is an admin in the channel.
* `BIN_CHANNEL`: A channel to the stream and download feature, add channel id and make bot admin in channel.
* `URL`: Add you deployed bot app link or vps IP address
### Optional Variables
* `AUTH_CHANNEL`: ID of force subscribe channels (Multiple channels can be used separated by space)
* `INDEX_CHANNELS`: Username or ID of your files channels (Multiple channels can be used separated by space)
* `LANGUAGES`: Language of your bot search (Multiple languages can be used separated by space)
* `TMDB_API_KEY`: API key for TMDb to get TMDb data. Get API key from [here](https://www.themoviedb.org/settings/api)
* `UPDATES_SEND_CHANNEL`: Channel ID for send updates if added new movie or tv series to database (Must need to add TMDB_API_KEY for send with TMDb info)
* Check [info.py](https://github.com/xHansaka-Anuhas/Nova-Filter-Bot/blob/main/info.py) for more optional variables


## Deploy
<details><summary>Deploy To Heroku</summary>

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy)

</details>

<details><summary>Deploy To Koyeb</summary>

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&builder=dockerfile&repository=https://github.com/xHansaka-Anuhas/Nova-Filter-Bot)

</details>

<details><summary>Deploy To Render</summary>

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

</details>

<details><summary>Deploy To VPS</summary>

1. Run the following command to ensure your system is up to date:
```
sudo apt update && sudo apt upgrade -y
```
2. If Docker is not already installed, install it using:
```
sudo apt install docker.io -y
```
3. Verify the installation:
```
docker --version
```
4. Ensure Docker starts on boot and is running:
```
sudo systemctl enable docker
sudo systemctl start docker
```
5. Clone this repository (also you can upload manually repo to your VPS):
```
git clone https://github.com/xHansaka-Anuhas/Nova-Filter-Bot
cd Auto-Filter-Bot
```
6. Navigate to your bot directory and build the Docker image:
```
sudo docker build -t auto-filter-bot .
```
7. Once the image is built, start the container:
```
sudo docker run -d -p 80:80 --name Auto-Filter-Bot auto-filter-bot
```
8. Verify that the bot is running:
```
sudo docker ps
```
9. If the bot crashes or needs to restart:
```
sudo docker restart Auto-Filter-Bot
```
10. If something is not working, check logs:
```
sudo docker logs Auto-Filter-Bot
```

</details>

## Support
* [![Support](https://img.shields.io/static/v1?label=Support&message=Group&color=critical)](https://t.me/Nova_Filter_Official)

## Credits
* [![EvaMaria](https://img.shields.io/static/v1?label=EvaMaria&message=Developers&color=critical)](https://t.me/TeamEvamaria)
* [![Hansaka](https://img.shields.io/static/v1?label=Hansaka&message=TG&color=critical)](https://t.me/Hansaka_Anuhas)
* [![Jules](https://img.shields.io/static/v1?label=Jules&message=AI%20Engineer&color=blueviolet)](https://github.com/Jules)

---
*Co-developed with love & expertise by Jules (AI Software Engineer Assistant).*

## Thanks To
* [Kurigram](https://github.com/KurimuzonAkuma/kurigram) For Telegram MTProto API Framework
* [Contributors](https://github.com/xHansaka-Anuhas/Nova-Filter-Bot/graphs/contributors) For free helps
* And to everyone who helped

## Note
* Importing this repo instead of forking is strictly prohibited, Kindly fork and edit as your wish. Must Give Credits for [developer(s)](https://t.me/Hansaka_Anuhas)
* If you find any bugs or errors, [report](https://t.me/Nova_Filter_Official) it

## Disclaimer
[![GNU General Public License v3.0](https://www.gnu.org/graphics/gplv3-with-text-136x68.png)](https://www.gnu.org/licenses/agpl-3.0.en.html#header)

* Licensed under [GNU AGPL v3.0](https://github.com/xHansaka-Anuhas/Nova-Filter-Bot/blob/main/LICENSE)
Selling The Codes To Other People For Money Is *Strictly Prohibited*.
