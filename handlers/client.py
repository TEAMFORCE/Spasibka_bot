from aiogram import types, Dispatcher
from create_bot import dp, bot
from api_requests import send_like, get_token, get_balance


# @dp.message_handler(commands=['баланс', 'balance'])
async def count(message: types.Message):
    '''
    Выводит в текущий чат количество спасибок у пользователя
    '''
    telegram_id = message.from_user.id
    group_id = message.chat.id
    telegram_name = message.from_user.username
    token = get_token(telegram_id, group_id, telegram_name)
    balance = get_balance(token)

    if balance == 'Что то пошло не так':
        await message.reply(balance)
    elif balance == 'Не найдена организация по переданному group_id':
        await message.reply(token)
    else:
        try:
            await message.reply(f"Заработанные спасибки: {int(balance['income']['amount'])}\n"
                                f"Спасибки для раздачи: {int(balance['distr']['amount'])}")
        except KeyError:
            await message.reply("Что то пошло не так")


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(count, commands=['баланс', 'balance'])
