from aiogram import types


def get_withdraw_amount(message: types.Message) -> int:
    """
    Get the amount of withdraw.
    """
    amount = message.text.replace("/withdraw ", "").replace(" ", "")
    try:
        return int(amount)
    except ValueError:
        return