from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from API.api_requests import user_organizations


def get_withdraw_info_keyboard(recipient_user_id: int, amount: int, callback_start_letter: str):
    """
    Yes/No keyboard for confirming currency withdraw.
    """
    returned_markup = InlineKeyboardMarkup(row_width=2)
    button_yes = InlineKeyboardButton(text='Yes',
                                      callback_data=f'{callback_start_letter} y {recipient_user_id} {amount}')
    button_no = InlineKeyboardButton(text='No',
                                     callback_data=f'{callback_start_letter} n {recipient_user_id} {amount}')
    returned_markup.add(button_yes, button_no)
    return returned_markup
