import asyncio

from aiogram import types, Dispatcher
from aiogram.dispatcher.filters.state import StatesGroup
from aiogram.utils.exceptions import MessageNotModified
from aiogram.dispatcher import FSMContext

from API.api_requests import get_token, get_active_organization, get_token_by_organization_id, get_user
from create_bot import user_req, bot, dp
from create_logger import logger
from dict_cloud.dicts import messages
from keyboards.inline_withdraw import get_withdraw_info_keyboard

from all_func.global_admin_keyboards import global_admin_keyboards


def get_withdraw_amount(message: types.Message) -> int:
    """
    Get the amount of withdraw.
    """
    amount = message.text.replace("/withdraw ", "").replace(" ", "")
    try:
        return int(amount)
    except ValueError:
        return


def get_user_token_and_organization_id(message: types.Message) -> (str, int, int):
    if message.chat.id != message.from_id:
        user = get_user(telegram_id=message.from_user.id,
                        group_id=message.chat.id,
                        telegram_name=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
        organization_id = user_req.get_organization_id_by_group_id(user['token'], message.chat.id)
    else:
        organization_id = get_active_organization(message.from_user.id)
        user = get_user(telegram_id=message.from_user.id,
                        telegram_name=message.from_user.username,
                        organization_id=organization_id,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
    print(user['token'], user['user_id'], organization_id)
    return user['token'], user['user_id'], organization_id


async def message_timeout_without_keyboard(message: types.Message, state: FSMContext, timeout: int = 60) -> None:
    """
    Check if message have markup and hide it.
    """
    await asyncio.sleep(timeout)
    if message.reply_markup:
        try:
            await message.edit_text('Скрыто по таймеру', reply_markup=None)
            await state.finish()
        except MessageNotModified:
            pass


async def set_state_and_send_approve_keyboard(message: types.Message, FSMWithdraw: StatesGroup, token: str,
                                              organization_id: int, amount: int) -> None:
    """
    Creates approval keyboard, set state for user to withdraw.
    """
    state = dp.current_state(chat=message.from_id, user=message.from_id)
    await state.set_state(FSMWithdraw.step_1)
    async with state.proxy() as data:
        data['token'] = token
        data['organization_id'] = organization_id
        data['amount'] = amount

    keyboard = get_withdraw_info_keyboard(message.from_id, amount, 'withdraw_proceed')
    temp_answer = await bot.send_message(message.from_id, f'Будет создан запрос на вывод {amount} спасибок.\n'
                                                          f'Продолжить?',
                                         reply_markup=keyboard)
    await message_timeout_without_keyboard(temp_answer, state)


async def withdraw_callback_yes_process(callback_query: types.CallbackQuery, recipient_token: str,
                                        organization_id: int) -> None:
    """
    Creates multiple keyboards for organization admins.
    """
    recipient_user_id = callback_query.data.split(' ')[2]
    amount = callback_query.data.split(' ')[3]
    await callback_query.message.edit_text(messages['withdraw']['request_sent'])
    logger.info(f'Запрос на вывод средств от id:{recipient_user_id} на {amount}')
    withdraw_request = user_req.create_withdraw_record(recipient_token, amount)
    if withdraw_request:
        admin_list = user_req.get_organization_admin_list(recipient_token, organization_id)
        confirm_keyboard = get_withdraw_info_keyboard(recipient_user_id,
                                                      amount,
                                                      'withdraw_request',
                                                      withdraw_request['details']['id'])
        for admin in admin_list:
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