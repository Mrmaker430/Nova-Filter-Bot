# Use @Get_emojiIDbot to get the premium emoji ID.
# Example of adding a premium emoji to message: "hello <emoji id='5210956306952758910'>👋</emoji> dear"
# If the ID (5210956306952758910) does not work, the normal emoji (👋) will be used as the default.
# The bot owner must have Telegram Premium to use premium emojis in the bot.

class script(object):

    START_TXT = """👋 <b>Hello {}, <i>{}</i></b>

<blockquote>🌟 <b>I am a high-performance Auto Filter & Link Shortener Bot.</b> Add me as an admin to your group or channel, and I will instantly deliver movies & TV series with smart buttons and fast cloud streaming links! 🚀</blockquote>"""

    MY_ABOUT_TXT = """🤖 <b>System Architecture & Info</b>

<blockquote>🖥️ <b>Server</b>: <a href="https://www.heroku.com">Cloud Engine</a>
🗄️ <b>Database</b>: <a href="https://www.mongodb.com">MongoDB Atlas</a>
🐍 <b>Language</b>: <a href="https://www.python.org">Python 3.11+</a>
⚡ <b>Framework</b>: <a href="https://kurigram.icu/">Kurigram Async</a></blockquote>"""

    MY_OWNER_TXT = """👨‍💻 <b>Developer & Owner Details</b>

<blockquote>🧑‍💻 <b>Lead Developer</b>: Satya Jit
💬 <b>Telegram</b>: @pArAd0X6
🛠️ <b>Support</b>: Available 24/7 via Support Group</blockquote>"""

    STATUS_TXT = """📊 <b>System Diagnostics</b>

<blockquote><b>👥 User & Group Metrics</b>
• 👤 Total Users: <code>{}</code>
• 😎 Premium Users: <code>{}</code>
• 👥 Total Connected Chats: <code>{}</code>

<b>🗄️ Data Database Status</b>
• 📦 DB Storage Used: <code>{}</code>

<b>🗳️ Primary Files Database</b>
• 🗂️ Indexed Files: <code>{}</code>
• 📦 Storage Used: <code>{}</code>

<b>🗳️ Secondary Files Database</b>
• 🗂️ Indexed Files: <code>{}</code>
• 📦 Storage Used: <code>{}</code>

<b>🚀 System Uptime</b>: <code>{}</code></blockquote>"""

    NEW_GROUP_TXT = """📌 <b>#NewGroup Connected</b>

🏷️ <b>Title</b>: {}
🆔 <b>ID</b>: <code>{}</code>
🔗 <b>Username</b>: {}
👥 <b>Total Members</b>: <code>{}</code>"""

    NEW_USER_TXT = """👤 <b>#NewUser Started Bot</b>

🧑 <b>Name</b>: {}
🆔 <b>ID</b>: <code>{}</code>"""

    NOT_FILE_TXT = """👋 <b>Hello {},</b>

<blockquote>🥲 <b>We couldn't locate any streaming or download files for:</b> <code>{}</code></blockquote>

<b>🔍 Why might this file be missing?</b>
• ✏️ <b>Spelling Error</b>: Check for typos or release year formatting.
• ⏳ <b>Not Released Yet</b>: The movie or season might not have digital availability.
• 🗂️ <b>Not Indexed</b>: We might still be processing or uploading this title.

<b>💡 Recommended Next Steps:</b>
• 🌐 Click <b>Search Google</b> below to verify exact movie/series names and release dates.
• 📖 Click <b>Instructions</b> below to see advanced search syntax tips.
• 📝 Type <code>/request Movie Name Year</code> directly in chat to notify our 24/7 upload team!"""
    
    IMDB_TEMPLATE = """🎬 <b>{title}</b> ({year})

<blockquote>🏷️ <b>Title</b>: <a href="{url}">{title}</a>
🎭 <b>Genres</b>: {genres}
🌟 <b>Rating</b>: <code>{rating} / 10</code>
☀️ <b>Languages</b>: {languages}
⏱️ <b>RunTime</b>: <code>{runtime} Min</code></blockquote>

🗣️ <b>Requested by</b>: {mention}
⚡ <b>Powered by</b>: <b>{group_title}</b>"""

    FILE_CAPTION = """📁 <b>{file_name}</b>

<blockquote>⚠️ <i>Please click the ✖️ Close button below once you have saved or downloaded this file!</i></blockquote>"""

    WELCOME_TEXT = """👋 <b>Hello {mention},</b>

<blockquote>✨ Welcome to <b>{title}</b>! We are glad to have you here. Type any movie or series name below to get instant download links! 💞</blockquote>"""

    HELP_TXT = """👋 <b>Hello {},</b>

<blockquote>✨ I am a high-performance Auto Filter & Link Shortener Bot designed to deliver instant movie & series files!</blockquote>

<b>🌟 Key Features & Capabilities:</b>
• 🔍 <b>Auto-Filter</b>: Type any movie/series name directly in PM or any connected group!
• ⚡ <b>Stream & Download</b>: Fast online streaming & direct cloud download links.
• 🔖 <b>Watchlist & Favorites</b>: Save files instantly with dedicated inline buttons.
• 🎯 <b>Smart Search</b>: Advanced Season & Episode filters with quality & language selectors.

<i>Explore all commands using the buttons below! 👇</i>"""

    ADMIN_COMMAND_TXT = """🛡️ <b>Admin Commands Panel</b>

<blockquote><b>⚙️ System & DB</b>
• 📊 /stats - Check system status
• 🔄 /restart - Reboot bot cleanly
• 🛠️ /repair_mode - Maintenance mode
• 🗳️ /index - Index channel files
• 📑 /index_channels - Indexed channels
• 🗑️ /delete - Delete files by query
• 💥 /delete_all - Wipe indexed DB

<b>📢 Broadcast & Groups</b>
• 📢 /broadcast - PM broadcast
• 📣 /grp_broadcast - Group broadcast
• 📌 /pin_broadcast - Pinned PM broadcast
• 📍 /pin_grp_broadcast - Pinned group broadcast
• 👥 /users - PM users stats
• 📁 /chats - Group chats stats
• 🚪 /leave - Leave group chat
• 🔗 /invite_link - Create invite link

<b>💎 VIP Premium & FSub</b>
• 👑 /add_prm - Grant VIP status
• 🚫 /rm_prm - Revoke VIP status
• 🛡️ /set_fsub - Force-Sub channels
• 🔔 /set_req_fsub - Request FSub channel
• 🧹 /delreq - Clear join requests</blockquote>"""
    
    PLAN_TXT = """💎 <b>Upgrade To Nova Premium</b>

<blockquote>Unlock exclusive VIP benefits and experience lightning-fast, ad-free file delivery without limits!</blockquote>

<b>🔥 Exclusive Premium Features:</b>
• 🚫 <b>100% Ad-Free Experience</b> (No shortlink redirects)
• ⚡ <b>Instant Watch & Download</b> (Stream online or fast direct download)
• 🔓 <b>No Force-Subscribe Required</b> (Skip channel joins)
• 🔖 <b>Unlimited Watchlist & Favorites</b>
• 💬 <b>Priority 24/7 Admin Support</b>

<b>🏷️ Available Subscription Tiers:</b>
<blockquote>{}</blockquote>

💬 <b>Ready to Upgrade?</b> Contact our support: @{}"""

    USER_COMMAND_TXT = """👤 <b>Bot User Commands Panel</b>

<blockquote><b>🎬 Search & Files</b>
• 🚀 /start - Check if bot is alive & active
• 🔖 /watchlist - View your saved Watchlist files
• ❤️ /favorites - View your saved Favorite files
• 📝 /request - Request a new movie or TV series
• 📥 /download - Download videos from YouTube, TikTok, FB & Insta

<b>⚙️ Settings & Group Control</b>
• ⚙️ /settings - Customize group filter preferences
• 🔗 /connect - Manage group settings from PM
• 🆔 /id - Check current group or channel ID

<b>💎 Premium & Utilities</b>
• 💎 /plan - View available premium subscription tiers
• 👑 /myplan - Check your active premium status & expiry
• 🖼️ /img_2_link - Upload an image to cloud & get URL</blockquote>"""
    
    SOURCE_TXT = """📂 <b>Open Source Repository</b>

<blockquote>🛠️ <b>Project</b>: Auto Filter Bot
🔗 <b>Repository</b>: <a href="https://github.com/">GitHub Repo</a>
🧑‍💻 <b>Lead Developer</b>: @pArAd0X6</blockquote>"""


    NEW_ADDED_TEMPLATE = """✅ <b>New Content Added</b>

<blockquote>🏷️ <b>Title</b>: <a href="{url}">{title}</a>
🎭 <b>Genres</b>: {genres}
📆 <b>Year</b>: {year}
🌟 <b>Rating</b>: <code>{rating} / 10</code>
☀️ <b>Languages</b>: {languages}
⏱️ <b>RunTime</b>: <code>{runtime} Min</code></blockquote>"""
