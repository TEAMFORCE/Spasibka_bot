import logging
import colorlog

from aiogram import Bot
from aiogram.dispatcher import Dispatcher

from censored import token_tg


bot = Bot(token=token_tg)
dp = Dispatcher(bot)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s:%(name)s:%(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white'
    }
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)