from logging import shutdown
from aiogram.utils import executor
from create_bot import dp
from database.database import create_tables


async def on_startup(_):
    '''
    Запуск бота
    '''
    print('Бот запущен')
    create_tables()
    print('БД создана')


from handlers import client, admin, other

admin.register_handlers_admin(dp)
client.register_handlers_client(dp)
other.register_handlers_other(dp)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=shutdown)
