from aiogram.dispatcher.filters.state import StatesGroup, State

from API.api_requests import get_token, get_token_by_organization_id, get_active_organization
from all_func.withdraw_utils import get_withdraw_amount
from create_bot import dp, bot, user_req
from create_logger import logger
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from dict_cloud.dicts import errors, messages
from keyboards.inline_withdraw import get_withdraw_info_keyboard


class FSMWithdraw(StatesGroup):
    step_1 = State()


@dp.message_handler(commands='withdraw')
async def withdraw(message: types.Message, state: FSMContext):
    amount = get_withdraw_amount(message)
    if not amount:
        await message.answer(errors['wrong_withdraw_amount'])
        return
    if message.chat.id != message.from_id:
        organization_id = user_req.get_organization_id_by_group_id(message.chat.id)
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
            await bot.send_message(message.from_id, f'Будет создан запрос на вывод {amount} спасибок.\nПродолжить ?',
                                 reply_markup=keyboard)
        else:
            await bot.send_message(message.from_id, errors['not_enough_currency']
                                 .format(available=account_check.get('errors').get('on_account')))
            await state.finish()
    else:
        await message.answer()
        await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('withdraw_proceed'), state=FSMWithdraw.step_1)
async def withdraw_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete_reply_markup()
    async with state.proxy() as data:
        token = data['token']
        organization_id = data['organization_id']
    data_list = callback_query.data.split(' ')
    recipient_user_id = data_list[2]
    amount = data_list[3]
    if data_list[1] == 'y':
        await callback_query.message.edit_text(messages['withdraw']['request_sent'])
        logger.info(f'Запрос на вывод средств от id:{recipient_user_id} на {amount}')
        user_req.create_withdraw_record(token, amount)
        admin_list = user_req.get_organization_admin_list(token, organization_id)
        confirm_keyboard = get_withdraw_info_keyboard(data_list[2], data_list[3], 'wd')
        for admin in admin_list[:1]:  # todo изменить срез когда будет готова логика для множественных клавиатур
            try:
                await bot.send_message(admin,
                                       f'Запрос на вывод средств от пользователя id:{callback_query.from_user.id}.\n'
                                       f'Подтверждаем ?',
                                       reply_markup=confirm_keyboard)
            except Exception as ex:
                logger.warning(f'Cant send request to {admin}. Error: {ex}')
    if data_list[1] == 'n':
        await callback_query.message.answer(messages['withdraw']['cancel'])


@dp.callback_query_handler(lambda c: c.data.startswith('wd/'))
async def withdraw_confirming(callback_query: types.CallbackQuery):
    await callback_query.message.delete_reply_markup()
    data_list = callback_query.data.split(' ')
    if data_list[1] == 'y':
        pass
    if data_list[1] == 'n':
        await callback_query.message.reply(messages['withdraw']['cancel'])
        await bot.send_message(data_list[2], messages['withdraw']['admin_cancel_withdraw'])


def register_handlers_withdraw(dp: Dispatcher):
    pass