from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

'''
Temp
'''
list_of_not_compited_transactions = ['transaction_1', 'transaction_2', 'transaction_3']
# todo по созданию эндпоинта добавить выгрузку транзакций, которые можно отменить

'''
Клавиатура для удаления транзакций
'''
not_complited_transactions = InlineKeyboardMarkup(row_width=1)
for i in list_of_not_compited_transactions:
    button = InlineKeyboardButton(text='🚫' + i, callback_data='delete ' + i)
    not_complited_transactions.add(button)

