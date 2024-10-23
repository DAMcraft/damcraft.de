import json
import os
from datetime import datetime

import requests


def get_discord_status():
    try:
        req = requests.get("https://api.lanyard.rest/v1/users/" + os.environ.get("DISCORD_ID")).json()
        return req.get("data", {}).get("discord_status", "")
    except requests.exceptions.RequestException:
        return None


def get_discord_invite():
    try:
        widget = (requests.get(
            f"https://discord.com/api/v9/guilds/{os.environ.get('SERVER_ID')}/widget.json"
        ).json())
        invite = widget.get("instant_invite")
        invite = invite.replace("https://discord.com/invite/", "https://discord.gg/")
        return invite
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError):
        return None


def get_age():
    birthday_str = os.environ.get("BIRTHDAY")  # YYYY-MM-DD
    if birthday_str is None:
        return None
    birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    has_passed = (today.month, today.day) >= (birthday.month, birthday.day)
    return today.year - birthday.year - (not has_passed)


def show_notification(blogs, request):
    if len(blogs) == 0:
        return None
    blog = blogs[0]
    cookie = request.cookies.get("last_read")
    if cookie == blog.url_name:
        return None
    return blog
