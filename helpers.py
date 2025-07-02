import base64
import json
import logging
import random
import re
import time
from datetime import datetime
from functools import lru_cache

import pytz
import requests
import unicodedata
from dateutil.relativedelta import relativedelta
from flask import send_from_directory, request

import const


def get_discord_status():
    try:
        req = requests.get("https://api.lanyard.rest/v1/users/" + str(const.DISCORD_ID)).json()
        return req.get("data", {}).get("discord_status", "")
    except requests.exceptions.RequestException:
        return None


def get_server_status(server_invite: str):
    try:
        # extract the invite code from the URL
        match = server_invite.split("/")[-1]
        req = requests.get(f"https://discord.com/api/v9/invites/{match}", timeout=5)
        req.raise_for_status()
        resp = req.json()
        icon_hash = resp.get("profile", {}).get("icon_hash", "")
        try:
            icon_bytes = requests.get(f"https://cdn.discordapp.com/icons/{const.SERVER_ID}/{icon_hash}.png").content
            icon = f"data:image/png;base64,{base64.b64encode(icon_bytes).decode('utf-8')}"
        except requests.exceptions.RequestException:
            icon = None
        return {
            "name": resp.get("profile", {}).get("name", ""),
            "icon": icon,
            "members": resp.get("profile", {}).get("member_count", 0),
            "online": resp.get("profile", {}).get("online_count", 0),
        }
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError):
        return None


def get_discord_invite():
    try:
        widget = (requests.get(
            f"https://discord.com/api/v9/guilds/{const.SERVER_ID}/widget.json"
        ).json())
        invite = widget.get("instant_invite")
        invite = invite.replace("https://discord.com/invite/", "https://discord.gg/")
        return invite
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError):
        return None


def get_age():
    birthday = datetime.strptime(const.BIRTHDAY, "%Y-%m-%d").date()
    today = datetime.now().date()
    return relativedelta(today, birthday).years


@lru_cache(maxsize=32)
def get_time_at_ip(ip: str) -> str | None:
    try:
        req = requests.get(f"https://ipinfo.io/{ip}?token={const.IP_INFO_API_KEY}").json()
        timezone = req.get("timezone", "UTC")
        time_there = datetime.now(pytz.timezone(timezone))
        return time_there.strftime("%I:%M")
    except requests.exceptions.RequestException:
        return None


def fishlogic():
    user_time = get_time_at_ip(request.remote_addr)
    if user_time == "11:11":
        return send_from_directory("assets/88x31", "makeafishtime.png")

    return send_from_directory("assets/88x31", "makeafish.png")


def format_iso_date(iso_timestamp):
    # Convert to datetime object
    date_obj = datetime.strptime(iso_timestamp, "%Y-%m-%d")

    # Get the day suffix
    day = date_obj.day
    suffix = "th" if 4 <= day <= 20 or 24 <= day % 10 <= 30 else "st" if day % 10 == 1 else "nd" if day % 10 == 2 else "rd"  # noqa

    # Format the date as "Month day_suffix Year"
    return date_obj.strftime(f"%B {day}{suffix}, %Y")


def show_notification(blogs, request):
    if len(blogs) == 0:
        return None
    blog = blogs.get_by_language("en")[0]
    cookie = request.cookies.get("last_read")
    if cookie == blog.url_name:
        return None
    return blog


def css_escape(s):
    s = s.replace("\0", "\uFFFD")  # replacement character

    s = re.sub(
        "[^A-Za-z0-9 _-]",
        lambda x: f"\\{ord(x.group(0)):x} ",
        s
    )

    return s


def timestamp_to_relative(timestamp: int):
    delta = time.time() - timestamp

    if delta < 60:
        return "just now"
    if delta < 60 * 60:
        return f"{int(delta / 60)} minute{'s' if delta // 60 > 1 else ''} ago"
    if delta < 60 * 60 * 24:
        return f"{int(delta / 60 / 60)} hour{'s' if delta / 60 // 60 > 1 else ''} ago"
    if delta < 60 * 60 * 24 * 7:
        return f"{int(delta / 60 / 60 / 24)} day{'s' if delta / 60 / 60 // 24 > 1 else ''} ago"

    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


def sanitize_comment(content):
    if not content or not content.strip():
        return

    if len(content.encode('utf-8')) > 2048 or len(content) > 1000:
        return
    content = ''.join(
        c for c in unicodedata.normalize("NFKC", content) if not unicodedata.combining(c)
    ).strip()
    return content


def smart_split(string, length):
    if len(string) <= length:
        return string
    end = string[:length].rsplit(" ", 1)[0]
    end = end.rstrip(",.:-")
    # if end is 25% shorter than cutting off the string, just cut it off
    if len(end) < len(string[:length]) * 0.75:
        return string[:length] + "..."
    return end + "..."


def random_copyright_year():
    years = [
        "1984",
        "1970",
        "1337",
        '<?php echo date("Y"); ?>',
        "$CURRENT_YEAR",
        "datetime.now().year",
        str(datetime.now().year + 1),
        "NULL",
        "NaN",
        "π",
        "random.randint(1900, 2100)",
        hex(datetime.now().year),
        "curl https://getfullyear.com/api/year"
    ]
    return random.choice(years)

