#credit dena toh de ni dena toh mat de laadle ~ GPG
import logging
from logging.handlers import RotatingFileHandler

LOG_FILE_NAME = "bot.log"
PORT = '8000'
OWNER_ID = 123456789
MSG_EFFECT = 5046509860389126442

# VPLink URL Shortener Configuration
VPLINK_API_TOKEN = "akenamebepuresososebandhadhaga"
VPLINK_API_URL = "example.com"

# URL Shortener Providers Configuration
URL_SHORTENERS = {
    'vplink': {
        'name': 'VPLink',
        'api_url': 'https://vplink.in/api',
        'api_token': VPLINK_API_TOKEN,
        'format': 'text',
        'active': True
    }
}

def LOGGER(name: str, client_name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        f"[%(asctime)s - %(levelname)s] - {client_name} - %(name)s - %(message)s",
        datefmt='%d-%b-%y %H:%M:%S'
    )
    file_handler = RotatingFileHandler(LOG_FILE_NAME, maxBytes=50_000_000, backupCount=10)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
