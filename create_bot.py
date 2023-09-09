from aiogram import Bot
from aiogram.dispatcher import Dispatcher

from API.api_requests import UserRequests
from censored import token_tg


bot = Bot(token=token_tg)
dp = Dispatcher(bot)

user_req = UserRequests()