from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Start dialogue"),
        types.BotCommand("balance", "Show balance"),
        types.BotCommand("tags", "Show awailables tags"),
        types.BotCommand("ct", "Cancel transaction"),
        types.BotCommand("go", "Change organization"),
        types.BotCommand("export", "Export account like"),
        types.BotCommand("rating", "List rating in organization"),
    ])