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


def create_scores_message(likes_list, user_likes):
    text = f"<b><u>Вами получено:</u></b> <code>{user_likes}</code>\n\n" \
           f"<b>Статистика по пользователям:</b>\n\n"
    sorted_likes_list = sorted(likes_list, key=lambda x: x['income_likes'], reverse=True)
    for i in sorted_likes_list:
        text += f"Пользователь: <code>{i['user']['tg_name']}</code>\n" \
                f"Рейтинг: <code>{i['income_likes']}</code>\n\n"
    return text
