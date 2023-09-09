from API.api_requests import get_token, get_token_by_organization_id, get_active_organization
from all_func.withdraw_utils import get_withdraw_amount
from create_bot import dp, bot, user_req
from create_logger import logger
from aiogram import types, Dispatcher

from dict_cloud.dicts import errors, messages
from keyboards.inline_withdraw import get_withdraw_info_keyboard


# @dp.message_handler(commands='withdraw')
async def withdraw(message: types.Message):
    amount = get_withdraw_amount(message)
    if not amount:
        await message.answer(errors['wrong_withdraw_amount'])
        return
    if message.chat.id != message.from_id:
        token = get_token(telegram_id=message.from_user.id, group_id=message.chat.id,
                          telegram_name=message.from_user.username, first_name=message.from_user.first_name,
                          last_name=message.from_user.last_name)

    else:
        organization_id = get_active_organization(message.from_user.id)
        token = get_token_by_organization_id(telegram_id=message.from_user.id,
                                             telegram_name=message.from_user.username,
                                             organization_id=organization_id,
                                             first_name=message.from_user.first_name,
                                             last_name=message.from_user.last_name)
    if not token:
        await message.answer(errors['cant_find_token'])
        return

    account_check = user_req.withdraw_amount_check(token, amount)

    if account_check:
        if account_check.get('status') == 0:
            keyboard = get_withdraw_info_keyboard(message.from_id, amount, 'w')
            await message.answer(f'Будет создан запрос на вывод {amount} спасибок.\nПродолжить ?',
                                 reply_markup=keyboard)
        else:
            await message.answer(errors['not_enough_currency']
                                 .format(available=account_check.get('errors').get('on_account')))
    else:
        await message.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('w '))
async def withdraw_callback(callback_query: types.CallbackQuery):
    await callback_query.message.delete_reply_markup()
    data_list = callback_query.data.split(' ')
    if data_list[1] == 'y':
        await callback_query.message.edit_text(messages['withdraw']['request_sent'])
        logger.info(f'Запрос на вывод средств от id:{data_list[2]} на {data_list[3]}')

        # todo запрос tg_id админов организации

        admin_id = 5148438149
        confirm_keyboard = get_withdraw_info_keyboard(data_list[2], data_list[3], 'wd')
        await bot.send_message(admin_id,
                               f'Запрос на вывод средств от пользователя id: {callback_query.message.from_id}.\n'
                               f'Подтверждаем ?',
                               reply_markup=confirm_keyboard)

    if data_list[1] == 'n':
        await callback_query.message.answer(messages['withdraw']['cancel'])


@dp.callback_query_handler(lambda c: c.data.startswith('wd '))
async def withdraw_confirming(callback_query: types.CallbackQuery):
    await callback_query.message.delete_reply_markup()
    data_list = callback_query.data.split(' ')
    if data_list[1] == 'y':
        pass
    if data_list[1] == 'n':
        await callback_query.message.reply(messages['withdraw']['cancel'])
        await bot.send_message(data_list[2], messages['withdraw']['admin_cancel_withdraw'])


def register_handlers_withdraw(dp: Dispatcher):
    dp.register_message_handler(withdraw, commands='withdraw')