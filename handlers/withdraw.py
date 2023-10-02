from aiogram.dispatcher.filters.state import StatesGroup, State

from API.api_requests import get_token_by_organization_id, get_active_organization, get_user
from all_func.withdraw_utils import get_withdraw_amount, get_user_token_and_organization_id, \
    set_state_and_send_approve_keyboard, withdraw_callback_yes_process
from create_bot import dp, bot, user_req
from create_logger import logger
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from dict_cloud.dicts import errors, messages

from all_func.global_admin_keyboards import global_admin_keyboards


class FSMWithdraw(StatesGroup):
    step_1 = State()


# @dp.message_handler(commands='withdraw')
async def withdraw(message: types.Message):
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
    await set_state_and_send_approve_keyboard(message, FSMWithdraw, token, organization_id, amount, user_id)


@dp.callback_query_handler(lambda c: c.data.startswith('withdraw_proceed'), state=FSMWithdraw.step_1)
async def withdraw_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete_reply_markup()
    async with state.proxy() as data:
        recipient_token = data['token']
        organization_id = data['organization_id']
        amount = data['amount']
        user_id = data['user_id']
    if callback_query.data.split(' ')[1] == 'y':
        account_check = user_req.withdraw_amount_check(recipient_token, amount)
        if account_check:
            if not account_check.get('status') == 0:
                await bot.send_message(callback_query.from_user.id, errors['not_enough_currency']
                                       .format(available=account_check.get('errors').get('on_account')))
                await state.finish()
                return
        await withdraw_callback_yes_process(callback_query, recipient_token, organization_id, user_id)
    if callback_query.data.split(' ')[1] == 'n':
        await callback_query.message.answer(messages['withdraw']['cancel'])
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('withdraw_request'))
async def withdraw_confirming(callback_query: types.CallbackQuery):
    data_list = callback_query.data.split(' ')
    recipient_tg_user_id = data_list[2]
    request_id = data_list[4]

    temp_dict = dict(global_admin_keyboards[recipient_tg_user_id])
    for admin, message in temp_dict.items():
        try:
            await message.edit_text(f'{message.text.replace("Подтверждаем ?", "")}\n'
                                    f'Администратор {callback_query.from_user.username} уже ответил на запрос',
                                    reply_markup=None)
            global_admin_keyboards[recipient_tg_user_id].pop(admin)
        except Exception as ex:
            logger.warning(f'Trying to delete markup but got exeption: {ex}')

    organization_id = get_active_organization(callback_query.from_user.id)
    token = get_token_by_organization_id(telegram_id=callback_query.from_user.id,
                                         telegram_name=callback_query.from_user.username,
                                         organization_id=organization_id,
                                         first_name=callback_query.from_user.first_name,
                                         last_name=callback_query.from_user.last_name)

    if data_list[1] == 'y':
        result = user_req.confirm_withdraw(token, request_id)
        if result['status'] == 0:
            await callback_query.message.reply(messages['withdraw']['confirmed_for_admin'])
            await bot.send_message(recipient_tg_user_id, messages['withdraw']['confirmed_for_user'])
        else:
            await callback_query.message.answer(errors['withdraw_error'])
            await bot.send_message(data_list[2], messages['withdraw']['admin_cancel_withdraw'])
            await callback_query.message.answer(f"<code>{result['errors']}</code>", parse_mode=types.ParseMode.HTML)

    elif data_list[1] == 'n':
        result = user_req.decline_withdraw(token, request_id)
        if result:
            await callback_query.message.reply(messages['withdraw']['cancel'])
            await bot.send_message(data_list[2], messages['withdraw']['admin_cancel_withdraw'])
        else:
            await callback_query.message.answer(errors['withdraw_error'])


def register_handlers_withdraw(dp: Dispatcher):
    pass