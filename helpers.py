import os
from datetime import datetime

import requests


def get_discord_status():
    try:
        req = requests.get("https://api.lanyard.rest/v1/users/" + os.environ.get("DISCORD_ID")).json()
        return req.get("data", {}).get("discord_status", "")
    except requests.exceptions.RequestException:
        return None


def get_server_count():
    try:
        server_count = requests.get("https://api.serverseeker.net/stats").json().get("server_count")
        return round(server_count / 10000) * 10000
    except requests.exceptions.RequestException:
        return None


def get_member_count_and_invite():
    try:
        member_count = requests.get(
            "https://discord.com/api/v9/guilds/1087081486747971705?with_counts=true",
            headers={"Authorization": "Bot " + os.environ.get("DISCORD_TOKEN")}
        ).json().get("approximate_member_count", 0)
        widget = (requests.get(
            "https://discord.com/api/v9/guilds/1087081486747971705/widget.json"
        ).json())
        return {"member_count": f"{member_count:,}", "instant_invite": widget.get("instant_invite")}
    except requests.exceptions.RequestException:
        return {"member_count": None, "instant_invite": None}


def get_age():
    birthday_str = os.environ.get("BIRTHDAY")  # YYYY-MM-DD
    if birthday_str is None:
        return None
    birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    has_passed = (today.month, today.day) >= (birthday.month, birthday.day)
    return today.year - birthday.year - (not has_passed)

