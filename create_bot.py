from aiogram import Bot
from aiogram.dispatcher import Dispatcher

from API.api_requests import UserRequests, ConfirmChallenge, GroupRequests
from censored import token_tg

from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()
bot = Bot(token=token_tg)
dp = Dispatcher(bot, storage=storage)

user_req = UserRequests()
conf_challenge = ConfirmChallenge()
group_req = GroupRequests()