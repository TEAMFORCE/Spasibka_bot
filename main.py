from aiogram.utils import executor
from create_bot import dp


async def on_startup(_):
    '''
    Запуск бота
    '''
    print('Бот запущен')


async  def on_shutdown(_):
    '''
    Завершение работы
    '''
    print('Бот отключен')


from handlers import client, admin, other

admin.register_handlers_admin(dp)
client.register_handlers_client(dp)
other.register_handlers_other(dp)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
