from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from censored import mobile_thx_app

'''
Клавиатура для перехода в webapp
'''

start_web_app = InlineKeyboardMarkup(row_width=1)
button = InlineKeyboardButton(text='Go app!', web_app=WebAppInfo(url=mobile_thx_app))
start_web_app.add(button)
