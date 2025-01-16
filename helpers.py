import base64
import json
import logging
import queue
import time
import traceback
from datetime import datetime
from json import JSONDecodeError

import pytz
import requests
import unicodedata
from flask import send_from_directory, request

import const


def get_discord_status():
    try:
        req = requests.get("https://api.lanyard.rest/v1/users/" + str(const.DISCORD_ID)).json()
        return req.get("data", {}).get("discord_status", "")
    except requests.exceptions.RequestException:
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
    birthday_str = const.BIRTHDAY  # YYYY-MM-DD
    if birthday_str is None:
        return None
    birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    has_passed = (today.month, today.day) >= (birthday.month, birthday.day)
    return today.year - birthday.year - (not has_passed)


def get_time_at_ip(ip: str) -> str | None:
    try:
        req = requests.get(f"https://ipinfo.io/{ip}?token={const.IP_INFO_API_KEY}").json()
        timezone = req.get("timezone", "UTC")
        time_there = datetime.now(pytz.timezone(timezone))
        return time_there.strftime("%H:%M")
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
    blog = blogs[0]
    cookie = request.cookies.get("last_read")
    if cookie == blog.url_name:
        return None
    return blog


def get_handlers() -> [logging.StreamHandler]:
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")

    # Create a handler for the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Create a handler for the file
    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    return console_handler, file_handler


def escape(s):
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\A")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    return s


def get_spotify_status(access_token):
    try:
        req = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers={
            "Authorization": f"Bearer {access_token}"
        })
        if req.status_code == 429:
            return {"error": {"status": 429, "retry_after": req.headers.get("Retry-After")}}
        return req.json()

    except (requests.exceptions.RequestException, JSONDecodeError):
        return None


def get_access_token():
    refresh_token = const.SPOTIFY_REFRESH_TOKEN
    client_id = const.SPOTIFY_CLIENT_ID
    client_secret = const.SPOTIFY_CLIENT_SECRET
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    response = requests.post("https://accounts.spotify.com/api/token", data=data, headers=headers)
    if response.status_code == 200:
        at = response.json().get("access_token")
        expires_on = datetime.now().timestamp() + response.json().get("expires_in")
        return at, expires_on
    return None, 0


def timestamp_to_relative(timestamp):
    date = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    delta = now - date

    if delta.total_seconds() < 60:
        return "just now"
    if delta.total_seconds() < 60 * 60:
        return f"{int(delta.total_seconds() / 60)} minutes ago"
    if delta.total_seconds() < 60 * 60 * 24:
        return f"{int(delta.total_seconds() / 60 / 60)} hours ago"
    if delta.total_seconds() < 60 * 60 * 24 * 7:
        return f"{int(delta.total_seconds() / 60 / 60 / 24)} days ago"
    return date.strftime("%Y-%m-%d")


def sanitize_comment(content):
    if not content or not content.strip():
        return

    if len(content.encode('utf-8')) > 2048 or len(content) > 1000:
        return
    content = ''.join(
        c for c in unicodedata.normalize("NFKC", content) if not unicodedata.combining(c)
    ).strip()
    return content


shared_event_queues = set()


def event_reader(start):
    event_queue = queue.Queue()
    shared_event_queues.add(event_queue)
    yield start
    yield last_event
    while True:
        event = event_queue.get()
        if event is None:
            break
        yield event


def event_writer(event):
    for q in shared_event_queues:
        try:
            q.put(event)
        except (queue.Full, RuntimeError, OSError):
            shared_event_queues.remove(q)


def spotify_status_updater():
    global access_token, expires_on, last_event
    last_state = None
    last_push = 0
    while True:
        if expires_on < time.time():
            access_token, expires_on = get_access_token()

        try:
            status = get_spotify_status(access_token)
            retry_after = 3
            if status and status.get("error", {}).get("status") == 429:
                retry_after = int(status.get("error", {}).get("retry_after", 3))
                if retry_after < 3:
                    retry_after = 3
                print(f"We are being rate limited, retrying after {retry_after} seconds")

            if status is None or "error" in status:
                data = f"""
                <div class="overwrite-div"></div>
                <style>
                    .notification-content {{
                        display: none;
                    }}
                    .not-playing {{
                        display: flex;
                    }}
                </style>
                """
                event_writer(data)
                last_event = data
                time.sleep(retry_after)
                continue

            song_title = status["item"]["name"]
            artist = ", ".join([artist["name"] for artist in status["item"]["artists"]])
            # get the first image that is at least 100x100
            covers = status["item"]["album"]["images"]
            cover = covers[0]["url"]  # default to the first image
            for cover_ in covers:
                if cover_["height"] >= 100 and cover_["width"] >= 100:
                    cover = cover_["url"]
            cover = cover.replace("https://i.scdn.co/image/", "https://damcraft.de/spotify-image-proxy/")
            progress = status["progress_ms"] // 1000
            duration = status["item"]["duration_ms"] // 1000
            song_url = status["item"]["external_urls"]["spotify"]
            is_playing = status["is_playing"]
            delta = duration - progress
            duration_str = f"{duration // 60}:{duration % 60:02d}"

            state = (song_title, artist, cover, duration, is_playing)
            if state == last_state and 0 <= progress - last_push <= 5:
                if not is_playing:
                    time.sleep(1.5)
                    continue
                continue
            last_state = state
            last_push = progress

            song_title = escape(song_title)
            artist = escape(artist)

            unique_id = str(time.time()).replace(".", "")
            seconds_keyframes = []
            minutes_keyframes = []
            for i in range(11):
                tmp_i = i
                if not is_playing:
                    tmp_i = 0
                if progress + tmp_i >= duration:
                    tmp_i = duration - progress
                seconds_keyframes.append(f"{i * 10}% {{ counter-increment: seconds{unique_id} {(progress + tmp_i) % 60}; }}")   # noqa
                minutes_keyframes.append(f"{i * 10}% {{ counter-increment: minutes{unique_id} {(progress + tmp_i) // 60}; }}")  # noqa
            seconds_keyframes = "\n".join(seconds_keyframes)
            minutes_keyframes = "\n".join(minutes_keyframes)

            data = f"""
            <div class="overwrite-div"></div>
            <a href="{song_url}" class="open-song" target="_blank"><div><img src="/assets/open.svg" alt="Open"></div></a>
            
            <style>
            .notification-content {{
                display: flex;
            }}
            .not-playing {{
                display: none;
            }}
                    
            .song-length::before {{
                content: "{duration_str}";
            }}
            
            .seconds-progress::before {{
                content: "0" counter(seconds{unique_id});
                animation: countSeconds{unique_id} 10s steps(10) forwards;
            }}
            @keyframes countSeconds{unique_id} {{
                {seconds_keyframes}
            }}
            .minutes-progress::before {{
                content: "0" counter(minutes{unique_id});
                animation: countMinutes{unique_id} 10s steps(10) forwards;
            }}
            @keyframes countMinutes{unique_id} {{
                {minutes_keyframes}
            }}
            
            .song-title::before {{
                content: "{song_title}";
            }}
            .song-artist::before {{
                content: "{artist}";
            }}
            .album-cover {{
                background-image: url({cover});
            }}
            .progress-bar::before {{
                width: {progress * 100 / duration}%;
                animation: progress{unique_id} {delta}s forwards;
            }}
            """
            if is_playing:
                data += f"""
                @keyframes progress{unique_id} {{
                    to {{
                        width: 100%;
                    }}
                }}
                
                .paused {{
                    visibility: hidden;
                }}
                """
            else:
                data += """
                .paused {
                    visibility: visible;
                }
                """

            data += "</style>"

            event_writer(data)
            last_event = data
        except BaseException:
            traceback.print_exc()
            pass
        time.sleep(1.5)


access_token, expires_on = get_access_token()
last_event = ""
