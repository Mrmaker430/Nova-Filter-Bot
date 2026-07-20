import re
from os import environ
import os
from Script import script
import logging

logger = logging.getLogger(__name__)

def is_enabled(type, value):
    data = environ.get(type, str(value))
    if data.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif data.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        logger.error(f'{type} is invalid, exiting now')
        exit()

def is_valid_ip(ip):
    ip_pattern = r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    return re.match(ip_pattern, ip) is not None

# Bot information
API_ID = environ.get('API_ID', '')
if len(API_ID) == 0:
    logger.error('API_ID is missing, exiting now')
    exit()
else:
    API_ID = int(API_ID)
API_HASH = environ.get('API_HASH', '')
if len(API_HASH) == 0:
    logger.error('API_HASH is missing, exiting now')
    exit()
BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    logger.error('BOT_TOKEN is missing, exiting now')
    exit()
BOT_ID = BOT_TOKEN.split(":")[0]
PORT = int(environ.get('PORT', '80'))

# Upload your images to "postimages.org" and get direct link
PICS = (environ.get('PICS', 'https://i.ibb.co/PzZNZHF6/IMG-20251116-113905-254.jpg https://i.ibb.co/8npWSZ5T/pic.jpg')).split()

# Bot Admins
ADMINS = environ.get('ADMINS', '1773034985')
if len(ADMINS) == 0:
    logger.error('ADMINS is missing, exiting now')
    exit()
else:
    ADMINS = [int(admins) for admins in ADMINS.split()]

# Channels
INDEX_CHANNELS = [int(index_channels) if index_channels.startswith("-") else index_channels for index_channels in environ.get('INDEX_CHANNELS', '-1002250750580 -1002640281126 -1002505289854 -1002453402856 -1002433218654 -1002357138941').split()]
if len(INDEX_CHANNELS) == 0:
    logger.info('INDEX_CHANNELS is empty')
LOG_CHANNEL = environ.get('LOG_CHANNEL', '-1002681646366')
if len(LOG_CHANNEL) == 0:
    logger.error('LOG_CHANNEL is missing, exiting now')
    exit()
else:
    LOG_CHANNEL = int(LOG_CHANNEL)
UPDATES_SEND_CHANNEL = environ.get('UPDATES_SEND_CHANNEL', '-1003784139938')
if len(UPDATES_SEND_CHANNEL) == 0:
    logger.info('UPDATES_SEND_CHANNEL is missing')
    UPDATES_SEND_CHANNEL = None
else:
    UPDATES_SEND_CHANNEL = int(UPDATES_SEND_CHANNEL)

REQUESTS_CHANNEL = environ.get('REQUESTS_CHANNEL', '-1003717648037')
if len(REQUESTS_CHANNEL) == 0:
    logger.info('REQUESTS_CHANNEL is missing, using LOG_CHANNEL')
    REQUESTS_CHANNEL = LOG_CHANNEL
else:
    REQUESTS_CHANNEL = int(REQUESTS_CHANNEL)

# support group
SUPPORT_GROUP = environ.get('SUPPORT_GROUP', '-1003717648037')
if len(SUPPORT_GROUP) == 0:
    SUPPORT_GROUP = None
    logger.warning('SUPPORT_GROUP is missing')
else:
    SUPPORT_GROUP = int(SUPPORT_GROUP)

# MongoDB information
DATA_DATABASE_URL = environ.get('DATA_DATABASE_URL', "")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Files') 
FILES_DATABASE_URL = environ.get('FILES_DATABASE_URL', "")
SECOND_FILES_DATABASE_URL = environ.get('SECOND_FILES_DATABASE_URL', "")
DATABASE_NAME = environ.get('DATABASE_NAME', "Cluster0")

if len(DATA_DATABASE_URL) == 0 and len(FILES_DATABASE_URL) == 0:
    logger.error('FILES_DATABASE_URL and DATA_DATABASE_URL are missing. You must provide at least one of them. Exiting now.')
    exit()
elif len(DATA_DATABASE_URL) == 0:
    DATA_DATABASE_URL = FILES_DATABASE_URL
    logger.warning('DATA_DATABASE_URL is missing, using FILES_DATABASE_URL as fallback.')
elif len(FILES_DATABASE_URL) == 0:
    FILES_DATABASE_URL = DATA_DATABASE_URL
    logger.warning('FILES_DATABASE_URL is missing, using DATA_DATABASE_URL as fallback.')

if len(SECOND_FILES_DATABASE_URL) == 0:
    logger.info('SECOND_FILES_DATABASE_URL is empty')


# Links
SUPPORT_LINK = environ.get('SUPPORT_LINK', 'https://t.me/cholochhitrosupport')
UPDATES_LINK = environ.get('UPDATES_LINK', 'https://t.me/')
FILMS_LINK = environ.get('FILMS_LINK', 'https://t.me/cholochhitro')
TUTORIAL = environ.get("TUTORIAL", "https://t.me/")
TUTORIAL_NAME = environ.get("TUTORIAL_NAME", "Tutorial")
VERIFY_TUTORIAL = environ.get("VERIFY_TUTORIAL", "https://t.me/")

# Bot settings
TIME_ZONE = environ.get('TIME_ZONE', 'Asia/Kolkata') # Replace your time zone
DELETE_TIME = int(environ.get('DELETE_TIME', 600)) # Add time in seconds
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
MAX_BTN = int(environ.get('MAX_BTN', 8))
LANGUAGES = [language.lower() for language in environ.get('LANGUAGES', 'hindi english telugu tamil kannada malayalam marathi punjabi').split()]
QUALITY = [quality.lower() for quality in environ.get('QUALITY', '360p 480p 720p 1080p 2160p').split()]
IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", script.IMDB_TEMPLATE)
FILE_CAPTION = environ.get("FILE_CAPTION", script.FILE_CAPTION)
SHORTLINK_URL = environ.get("SHORTLINK_URL", "mdiskshortner.link")
SHORTLINK_API = environ.get("SHORTLINK_API", "36f1ae74ba1aa01e5bd73bdd0bc22aa915443501")
VERIFY_EXPIRE = int(environ.get('VERIFY_EXPIRE', 86400)) # Add time in seconds
WELCOME_TEXT = environ.get("WELCOME_TEXT", script.WELCOME_TEXT)
INDEX_EXTENSIONS = [extensions.lower() for extensions in environ.get('INDEX_EXTENSIONS', 'mp4 mkv').split()]
PM_FILE_DELETE_TIME = int(environ.get('PM_FILE_DELETE_TIME', '3600'))

# boolean settings
USE_CAPTION_FILTER = is_enabled('USE_CAPTION_FILTER', False)
IS_VERIFY = is_enabled('IS_VERIFY', False)
AUTO_DELETE = is_enabled('AUTO_DELETE', False)
WELCOME = is_enabled('WELCOME', False)
PROTECT_CONTENT = is_enabled('PROTECT_CONTENT', False)
LONG_IMDB_DESCRIPTION = is_enabled("LONG_IMDB_DESCRIPTION", False)
LINK_MODE = is_enabled("LINK_MODE", True)
IMDB = is_enabled('IMDB', True)
SPELL_CHECK = is_enabled("SPELL_CHECK", True)
SHORTLINK = is_enabled('SHORTLINK', False)
AUTO_FILTER = is_enabled('AUTO_FILTER', True)
PM_SEARCH = is_enabled('PM_SEARCH', False)

# bot string settings
FORCE_SUB_CHANNELS = environ.get('FORCE_SUB_CHANNELS', '-1002097884361')  # For multiple channels, separate channel IDs with spaces. Example: "-100xxxxx -100xxxxx -100xxxxx"
REQUEST_FORCE_SUB_CHANNEL = environ.get('REQUEST_FORCE_SUB_CHANNEL', '-1003784139938')

# for stream
IS_STREAM = is_enabled('IS_STREAM', True)
BIN_CHANNEL = environ.get("BIN_CHANNEL", "-1002681646366")
if len(BIN_CHANNEL) == 0:
    logger.error('BIN_CHANNEL is missing, exiting now')
    exit()
else:
    BIN_CHANNEL = int(BIN_CHANNEL)
URL = environ.get("URL", "")
if len(URL) == 0:
    logger.error('URL is missing, exiting now')
    exit()
else:
    if URL.startswith(('https://', 'http://')):
        if not URL.endswith("/"):
            URL += '/'
    elif is_valid_ip(URL):
        URL = f'http://{URL}/'
    else:
        logger.error('URL is not valid, exiting now')
        exit()

#start command reactions 
REACTIONS = [reactions for reactions in environ.get('REACTIONS', '🤝 😇 🤗 😍 👍 🎅 😐 🥰 🤩 😱 🤣 😘 👏 😛 😈 🎉 ⚡️ 🫡 🤓 😎 🏆 🔥 🤭 🌚 🆒 👻 😁').split()]  # Multiple reactions can be used separated by space
EFFECT_IDS = [effect for effect in environ.get('EFFECT_IDS', '5104841245755180586 5104858069142078462 5159385139981059251 5046509860389126442 5046589136895476101 5107584321108051014').split()]

# for Premium 
IS_PREMIUM = is_enabled('IS_PREMIUM', True)
OWNER_USERNAME = environ.get("OWNER_USERNAME", "pArAd0X6")
PAYMENT_QR_CODE = "https://i.postimg.cc/4xmm21x5/qr-code.jpg" # add your payment qr code link, like upi qr code or any crypto qr code link
PAYMENT_ID = "mypayment@id"  # add your payment id like upi id or crypto address

# Format -- Days: ['CURRENCY', Price]
PREMIUM_PLANS = {
    7: ['USD', 1], 
    14: ['USD', 2],
    30: ['USD', 3],
    365: ['USD', 10]
}
PAYMENT_TYPE = "UPI"  # can be changed to "Crypto (TRC20)" or "PayPal" or etc....


# for TMDb
TMDB_API_KEY = environ.get("TMDB_API_KEY", "98f215cdc731a595c9d36dadca08a1aa")  # Get API key from here - https://www.themoviedb.org/settings/api
if len(TMDB_API_KEY) == 0:
    logger.info('TMDB_API_KEY is missing')
    TMDB_API_KEY = None
