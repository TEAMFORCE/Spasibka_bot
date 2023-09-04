from API.api_requests import all_like_tags


def find_tag_id(pattern_tag, token: str) -> str:
    tag = pattern_tag.group(1).lower().replace("_", " ")
    all_tags = all_like_tags(user_token=token)
    for i in all_tags:
        if i['name'].lower() == tag:
            return str(i['id'])