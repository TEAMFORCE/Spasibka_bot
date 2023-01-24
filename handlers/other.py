from aiogram import types, Dispatcher
from create_bot import dp, bot
from API.api_requests import send_like, get_token
from database.database import deactivate_all, activate_org
import re
import time
import asyncio


# @dp.message_handler(content_types=['text'])
async def likes(message: types.Message):
    '''
    При получении сообщения начинающегося с '+' отправляет лайки пользователю цитируемого сообщения
    :param message: Формат: +n 'необязательное сообщение', n-количество спасибок
    :return:
    '''
    if message.text.startswith('+'):
        pattern = r'\+(\d*)(.*)'
        likes = re.match(pattern, message.text).group(1)
        other = re.match(pattern, message.text).group(2)

        telegram_id = message.from_user.id
        group_id = str(message.chat.id)
        telegram_name = message.from_user.username
        token = get_token(telegram_id, group_id, telegram_name)

        telegram_id = str(message.reply_to_message.from_user.id)
        telegram_name = message.reply_to_message.from_user.username
        amount = likes

        result = send_like(token, telegram_id, telegram_name, amount)

        if result == 'Спасибка отправлена':
            await message.reply(f'Перевод на {amount} для @{telegram_name} сформирован')
        else:
            await message.reply(result)


# @dp.callback_query_handler(lambda c: c.data.startswith('delete '))
async def delete_transaction(callback_query: types.CallbackQuery):
    await callback_query.answer(f'Отменяем транзакцию {callback_query.data.split(" ")[1]}')
    await bot.edit_message_text(f'Транзакция {callback_query.data.split(" ")[1]} отменена',
                                chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id)
    # todo по созданию эндпоинта добавить отмену транзакции по идентификатору


# @dp.callback_query_handler(lambda c: c.data.startswith('org '))
async def change_active_organization(callback_query: types.CallbackQuery):
    await callback_query.answer(f'Активируем {callback_query.data.split(" ")[1]}')
    deactivate_all(tg_id=callback_query.from_user.id)
    activate_org(tg_id=callback_query.from_user.id, org_id=callback_query.data.split(" ")[1])
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, f'Текущая организация изменена на {callback_query.data.split(" ")[2]}')


def register_handlers_other(dp: Dispatcher):
    dp.register_message_handler(likes, content_types=['text'])
    dp.register_callback_query_handler(delete_transaction, lambda c: c.data.startswith('delete '))
    dp.register_callback_query_handler(change_active_organization, lambda c: c.data.startswith('org '))
