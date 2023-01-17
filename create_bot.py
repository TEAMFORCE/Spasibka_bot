from aiogram import Bot
from aiogram.dispatcher import Dispatcher

from censored import token_tg


bot = Bot(token=token_tg)
dp = Dispatcher(bot)

