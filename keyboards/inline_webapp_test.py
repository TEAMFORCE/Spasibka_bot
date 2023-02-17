from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

'''
Клавиатура для перехода в webapp
'''

start_web_app = InlineKeyboardMarkup(row_width=1)
button = InlineKeyboardButton(text='Go app!', web_app=WebAppInfo(url="https://mallwms.com:3000/"))
start_web_app.add(button)
