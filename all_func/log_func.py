from datetime import date, timedelta
import os


async def create_transaction_log(**kwargs):
    today = date.today()
    one_month = timedelta(30)
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
        print("Log added")
    # Удаляем фаил
    file_path = fr"Transactions_{today - one_month}.txt"
    try:
        os.unlink(file_path)
        print("Log deleted")
    except FileNotFoundError:
        pass
    os.chdir("..")
