from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

'''
Temp
'''

'''
Клавиатура для удаления транзакций
'''


def get_not_complited_transactions_kb(list_of_canceleble_likes: list):
    """
    Формирует клавиатуру со спасибками, готовыми к отмене
    """
    not_complited_transactions = InlineKeyboardMarkup(row_width=1)
    for i in list_of_canceleble_likes:
        button = InlineKeyboardButton(text=f'🚫 + {str(i["amount"])} to {i["recipient"]}',
                                      callback_data=f'delete {i["id"]} {i["organization"]}'
                                      )
        not_complited_transactions.add(button)
    return not_complited_transactions
