import base64
import json
import os
import queue
import time
import traceback
from datetime import datetime
from json import JSONDecodeError

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


def format_iso_date(iso_timestamp):
    # Convert to datetime object
    date_obj = datetime.strptime(iso_timestamp, "%Y-%m-%d")

    # Get the day suffix
    day = date_obj.day
    suffix = "th" if 4 <= day <= 20 or 24 <= day % 10 <= 30 else "st" if day % 10 == 1 else "nd" if day % 10 == 2 else "rd"

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
    refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
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
            retry_after = 2
            if status and status.get("error", {}).get("status") == 429:
                retry_after = int(status.get("error", {}).get("retry_after", 2))

            if status is None or "error" in status:
                data = f"""
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
            cover = status["item"]["album"]["images"][0]["url"]
            progress = status["progress_ms"] // 1000
            duration = status["item"]["duration_ms"] // 1000
            is_playing = status["is_playing"]
            delta = duration - progress
            duration_str = f"{duration // 60}:{duration % 60:02d}"

            state = (song_title, artist, cover, duration, is_playing)
            if state == last_state and 0 <= progress - last_push <= 5:
                continue
            last_state = state
            last_push = progress

            song_title = song_title.replace('"', '\\"').replace("\\", "\\\\")
            artist = artist.replace('"', '\\"').replace("\\", "\\\\")

            unique_id = str(time.time()).replace(".", "")
            seconds_keyframes = []
            minutes_keyframes = []
            for i in range(11):
                tmp_i = i
                if not is_playing:
                    tmp_i = 0
                seconds_keyframes.append(f"{i * 10}% {{ counter-increment: seconds{unique_id} {(progress + tmp_i) % 60}; }}")
                minutes_keyframes.append(f"{i * 10}% {{ counter-increment: minutes{unique_id} {(progress + tmp_i) // 60}; }}")
            seconds_keyframes = "\n".join(seconds_keyframes)
            minutes_keyframes = "\n".join(minutes_keyframes)

            data = f"""<style>
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
        time.sleep(1)


access_token, expires_on = get_access_token()
last_event = ""
