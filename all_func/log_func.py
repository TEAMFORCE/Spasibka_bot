from datetime import date, timedelta
import os

from create_logger import logger


async def create_transaction_log(**kwargs):
    days_to_expire = 30
    today = date.today()
    one_month = timedelta(days_to_expire)
    temp = f"--- *** ---\n" \
           f"New transaction:\n" \
           f"user_token: {kwargs.get('user_token')}\n" \
           f"group_id: {kwargs.get('group_id')}\n" \
           f"telegram_id: {kwargs.get('telegram_id')}\n" \
           f"telegram_name: {kwargs.get('telegram_name')}\n" \
           f"amount: {kwargs.get('amount')}\n" \
           f"tag_id: {kwargs.get('tags')}\n" \
           f"reason: {kwargs.get('reason')}\n" \
           f"Response code: {kwargs.get('response_code')}\n\n"
    os.chdir("transaction_logs")
    with open(f"Transactions_{today}.txt", "a", encoding="utf-8") as log:
        log.write(temp)
        logger.info("Log added")
    # Удаляем фаил
    file_path = fr"Transactions_{today - one_month}.txt"
    try:
        os.unlink(file_path)
        logger.info(f"Log deleted due time expires ({days_to_expire} days)")
    except FileNotFoundError:
        pass
    os.chdir("..")
