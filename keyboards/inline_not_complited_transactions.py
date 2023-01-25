from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

'''
Temp
'''

'''
Клавиатура для удаления транзакций
'''


def get_not_complited_transactions_kb(user_token: str, list_of_canceleble_likes: list):
    '''
    Формирует клавиатуру со спасибками, готовыми к отмене
    '''
    list_of_not_compited_transactions = [{'amount': '1', 'recipient': 'brukva2', 'id': 3206}, {'amount': '1', 'recipient': 'brukva2', 'id': 3205}]
    not_complited_transactions = InlineKeyboardMarkup(row_width=1)
    for i in list_of_canceleble_likes:
        button = InlineKeyboardButton(text=f'🚫 + {str(i["amount"])} to {i["recipient"]}',
                                      callback_data=f'delete {i["id"]} {i["organization"]}'
                                      )
        not_complited_transactions.add(button)
    return not_complited_transactions

