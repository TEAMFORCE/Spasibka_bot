from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from API.api_requests import user_organizations

"""
Клавиатура для вывода организаций
"""


def get_user_organization_keyboard(telegram_id: str,
                                   tg_name: str = None,
                                   first_name: str = None,
                                   last_name: str = None):
    organiization_list = user_organizations(telegram_id, tg_name, first_name, last_name)
    user_organizations_kb = InlineKeyboardMarkup(row_width=2)
    for i in organiization_list:
        if i['is_current']:
            button = InlineKeyboardButton(
                text=i['name'] + ' ✅',
                callback_data='org ' + str(i['id']) + " " + "test")  # i['name'].replace(" ", "_"))
            user_organizations_kb.add(button)
        else:
            button = InlineKeyboardButton(
                text=i['name'],
                callback_data='org ' + str(i['id']) + " " + "test")  # i['name'].replace(" ", "_"))
            user_organizations_kb.add(button)
    return user_organizations_kb
