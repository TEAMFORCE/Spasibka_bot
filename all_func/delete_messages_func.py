import asyncio
from contextlib import suppress

from aiogram import types
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound

from API.api_requests import messages_lifetime
from dict_cloud.dicts import sleep_timer


async def delete_command(command: types.Message, group_id: int) -> None:
    """
    Удаляет только команду в соответствии с настройками сервера.
    """
    lifetime_dict = messages_lifetime(group_id)
    if not lifetime_dict:
        lifetime_dict = {'bot_messages_lifetime': sleep_timer, 'bot_commands_lifetime': sleep_timer}
    if lifetime_dict["bot_commands_lifetime"] != 0:
        await asyncio.sleep(lifetime_dict["bot_messages_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await command.delete()
    else:
        return


async def delete_message_bot_answer(answer, group_id):
    """
    Удаляет только одно сообщение от бота, в соответствии с настройками сервера
    """
    lifetime_dict = messages_lifetime(group_id)
    if not lifetime_dict:
        lifetime_dict = {'bot_messages_lifetime': 10, 'bot_commands_lifetime': 3}
    if lifetime_dict["bot_messages_lifetime"] != 0:
        await asyncio.sleep(lifetime_dict["bot_messages_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await answer.delete()
    else:
        return


async def delete_message_and_command(message: list[types.Message], group_id: str = None):
    """
    Вычисляет время жизни сообщений относительно настроек группы и удаляет их
    В message передается список ["команда", "ответ"]
    """
    lifetime_dict = messages_lifetime(group_id)

    if not lifetime_dict:
        lifetime_dict = {'bot_messages_lifetime': sleep_timer, 'bot_commands_lifetime': sleep_timer}

    if lifetime_dict['bot_messages_lifetime'] == 0 and lifetime_dict['bot_commands_lifetime'] != 0:
        await asyncio.sleep(lifetime_dict["bot_commands_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[0].delete()
        return
    elif lifetime_dict['bot_commands_lifetime'] == 0 and lifetime_dict['bot_messages_lifetime'] != 0:
        await asyncio.sleep(lifetime_dict["bot_messages_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[1].delete()
        return
    elif lifetime_dict['bot_messages_lifetime'] == 0 and lifetime_dict['bot_commands_lifetime'] == 0:
        return

    if lifetime_dict["bot_messages_lifetime"] > lifetime_dict["bot_commands_lifetime"]:
        await asyncio.sleep(lifetime_dict["bot_commands_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[0].delete()
        sleep_rest = lifetime_dict["bot_messages_lifetime"] - lifetime_dict["bot_commands_lifetime"]
        await asyncio.sleep(sleep_rest)
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[1].delete()
    if lifetime_dict["bot_messages_lifetime"] < lifetime_dict["bot_commands_lifetime"]:
        await asyncio.sleep(lifetime_dict["bot_messages_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[1].delete()
        sleep_rest = lifetime_dict["bot_commands_lifetime"] - lifetime_dict["bot_messages_lifetime"]
        await asyncio.sleep(sleep_rest)
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[0].delete()
    else:
        await asyncio.sleep(lifetime_dict["bot_commands_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            for i in message:
                await i.delete()