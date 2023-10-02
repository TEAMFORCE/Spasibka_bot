

def get_body_of_get_balance(telegram_id: int, tg_name: str = None, group_id: int = None,
                            organization_id: int = None) -> dict:
    """
    Creates dict body for get_balance request.
    """
    if organization_id and tg_name:
        body = {
            "telegram_id": telegram_id,
            "tg_name": tg_name,
            "group_id": group_id,
            "organization_id": organization_id
        }
    elif organization_id and not tg_name:
        body = {
            "telegram_id": telegram_id,
            "group_id": group_id,
            "organization_id": organization_id
        }
    elif not organization_id and tg_name:
        body = {
            "telegram_id": telegram_id,
            "group_id": group_id,
            "organization_id": organization_id
        }
    else:
        body = {
            "telegram_id": telegram_id,
            "group_id": group_id
        }
    return body
