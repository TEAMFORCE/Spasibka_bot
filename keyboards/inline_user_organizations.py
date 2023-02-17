from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from API.api_requests import user_organizations
from database.database import get_all_organizations

'''
Temp
'''

organization_list = [{'name': '007', 'id': 49}, {'name': 'ruDemo', 'id': 69}, {'name': 'TeamForce', 'id': 1}]

'''
Клавиатура для вывода организаций
'''


def get_user_organization_keyboard(telegram_id):
    organiization_list = user_organizations(telegram_id)
    user_organizations_kb = InlineKeyboardMarkup(row_width=2)
    for i in organiization_list:
        if i['is_current']:
            button = InlineKeyboardButton(
                text=i['name'] + ' ✅',
                callback_data='org ' + str(i['id']) + " " + i['name'])
            user_organizations_kb.add(button)
        else:
            button = InlineKeyboardButton(
                text=i['name'],
                callback_data='org ' + str(i['id']) + " " + i['name'])
            user_organizations_kb.add(button)
    return user_organizations_kb
