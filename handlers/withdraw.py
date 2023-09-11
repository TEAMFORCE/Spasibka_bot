import asyncio

from aiogram.dispatcher.filters.state import StatesGroup, State

from API.api_requests import get_token, get_token_by_organization_id, get_active_organization, get_user
from all_func.withdraw_utils import get_withdraw_amount, get_user_token_and_organization_id, \
    message_timeout_without_keyboard
from create_bot import dp, bot, user_req
from create_logger import logger
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from dict_cloud.dicts import errors, messages
from keyboards.inline_withdraw import get_withdraw_info_keyboard


global_admin_keyboards = {
    'group': {
        'key': 'value'
    }
}


class FSMWithdraw(StatesGroup):
    step_1 = State()


@dp.message_handler(commands='withdraw')
async def withdraw(message: types.Message, state: FSMContext):
    amount = get_withdraw_amount(message)
    if not amount:
        await message.answer(errors['wrong_withdraw_amount'])
        return
    token, user_id, organization_id = get_user_token_and_organization_id(message)
    if not token:
        await message.answer(errors['cant_find_token'])
        return
    if not organization_id:
        await message.answer(errors['no_organizations'])
        return
    await FSMWithdraw.step_1.set()
    async with state.proxy() as data:
        data['token'] = token
        data['organization_id'] = organization_id

    account_check = user_req.withdraw_amount_check(token, amount)

    if account_check:
        if account_check.get('status') == 0:
            keyboard = get_withdraw_info_keyboard(message.from_id, amount, 'withdraw_proceed')
            temp_answer = await bot.send_message(message.from_id, f'Будет создан запрос на вывод {amount} спасибок.\n'
                                                                  f'Продолжить?',
                                                                  reply_markup=keyboard)
            await message_timeout_without_keyboard(temp_answer)
        else:
            await bot.send_message(message.from_id, errors['not_enough_currency']
                                 .format(available=account_check.get('errors').get('on_account')))
            await state.finish()
    else:
        await message.answer(errors['withdraw_account_check_error'])
        await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('withdraw_proceed'), state=FSMWithdraw.step_1)
async def withdraw_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete_reply_markup()
    async with state.proxy() as data:
        recipient_token = data['token']
        organization_id = data['organization_id']
    data_list = callback_query.data.split(' ')
    recipient_user_id = data_list[2]
    amount = data_list[3]
    if data_list[1] == 'y':
        await callback_query.message.edit_text(messages['withdraw']['request_sent'])
        logger.info(f'Запрос на вывод средств от id:{recipient_user_id} на {amount}')
        withdraw_request = user_req.create_withdraw_record(recipient_token, amount)
        if withdraw_request:
            admin_list = user_req.get_organization_admin_list(recipient_token, organization_id)
            confirm_keyboard = get_withdraw_info_keyboard(data_list[2],
                                                          data_list[3],
                                                          'withdraw_request',
                                                          withdraw_request['details']['id'])
            logger.info(global_admin_keyboards)
            for admin in admin_list:  # todo изменить срез когда будет готова логика для множественных клавиатур
                try:
                    global_admin_keyboards.setdefault(recipient_user_id, {})
                    keyboard = await bot.send_message(admin,
                                           f'Запрос на вывод средств от пользователя '
                                           f'{callback_query.from_user.get_mention(as_html=True)}.\n'
                                           f'Подтверждаем ?',
                                           reply_markup=confirm_keyboard, parse_mode=types.ParseMode.HTML)
                    global_admin_keyboards[recipient_user_id].setdefault(admin, keyboard)
                except Exception as ex:
                    logger.warning(f'Cant send request to {admin}. Error: {ex}')
            logger.info(global_admin_keyboards)
    if data_list[1] == 'n':
        await callback_query.message.answer(messages['withdraw']['cancel'])
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('withdraw_request'))
async def withdraw_confirming(callback_query: types.CallbackQuery):
    data_list = callback_query.data.split(' ')
    recipient_tg_user_id = data_list[2]
    request_id = data_list[4]
    logger.info(global_admin_keyboards)
    temp_dict = dict(global_admin_keyboards[recipient_tg_user_id])
    for admin, message in temp_dict.items():
        try:
            await message.delete_reply_markup()
            global_admin_keyboards[recipient_tg_user_id].pop(admin)
        except Exception as ex:
            logger.warning(f'Trying to delete markup but got exeption: {ex}')

    logger.info(global_admin_keyboards)
    organization_id = get_active_organization(callback_query.from_user.id)
    token = get_token_by_organization_id(telegram_id=callback_query.from_user.id,
                                         telegram_name=callback_query.from_user.username,
                                         organization_id=organization_id,
                                         first_name=callback_query.from_user.first_name,
                                         last_name=callback_query.from_user.last_name)
    if data_list[1] == 'y':
        result = user_req.confirm_withdraw(token, request_id)
        if result:
            await callback_query.message.reply(messages['withdraw']['confirmed_for_admin'])
            await bot.send_message(recipient_tg_user_id, messages['withdraw']['confirmed_for_user'])
        else:
            await callback_query.message.answer(errors['withdraw_error'])
    elif data_list[1] == 'n':
        result = user_req.decline_withdraw(token, request_id)
        if result:
            await callback_query.message.reply(messages['withdraw']['cancel'])
            await bot.send_message(data_list[2], messages['withdraw']['admin_cancel_withdraw'])
        else:
            await callback_query.message.answer(errors['withdraw_error'])


def register_handlers_withdraw(dp: Dispatcher):
    pass