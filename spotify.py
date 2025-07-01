import base64
import hashlib
import hmac
import json
import threading
import time
from datetime import datetime
from json import JSONDecodeError

import requests
from gevent import queue, lock
import traceback
from typing import Literal
import bs4
from gevent.timeout import Timeout
from playwright.sync_api import sync_playwright

import const
from helpers import css_escape

shared_event_queues = set()
queue_lock = lock.RLock()


class Lyrics:
    def __init__(self, lines):
        # sort lines by timestamp
        self.lyrics = {}
        for timestamp, words in lines.items():
            self.lyrics[timestamp] = words
        self.lyrics = dict(sorted(self.lyrics.items()))

    def get_last_lyrics(self, timestamp: float):
        # last where <= timestamp
        latest_line = "", 0
        for ts, line in self.lyrics.items():
            if ts <= timestamp:
                latest_line = line
            else:
                break
        return latest_line

    # def get_all_next_lyrics(self, timestamp: float):
    #     # all where > timestamp
    #     new = {timestamp: self.get_last_lyrics(timestamp)}
    #     new.update({ts: line for ts, line in self.lyrics.items() if ts > timestamp})
    #     print(new)
    #     return new


def build_lyrics_css(lyrics: Lyrics | None, progress: float, duration: float, is_playing: bool) -> str:
    if lyrics is None or not is_playing:
        return ".song-lyrics { display: none; } .song-lyrics::after { animation: none; }"
    unique_id = str(time.time()).replace(".", "")
    lyrics_css = [
        f".song-lyrics::after {{ animation: lyrics{unique_id} {duration}s steps(1) forwards; ",
        f"animation-delay: {-progress}s; }}",
        f"@keyframes lyrics{unique_id} {{"
    ]

    for ts, line in lyrics.lyrics.items():
        progress_percentage = ts * 100 / duration
        lyrics_css.append(f"{progress_percentage}% {{ content: '{css_escape(line)}'; }}")
    lyrics_css.append("}")

    lyrics_css.append(".song-lyrics { display: block; }")
    lyrics_css = "\n".join(lyrics_css)
    return lyrics_css


def generate_spotify_totp():
    try:
        # thank you https://github.com/KRTirtho/spotube/commit/59f298a935c87077a6abd50656f8a4ead44bd979 <3
        # req = requests.get("https://open.spotify.com/server-time")
        # time_interval = req.json()["serverTime"] // 30
        time_interval = int(time.time() // 30)

        hmac_hash = hmac.new(
            key=b'5507145853487499592248630329347',
            msg=time_interval.to_bytes(8, "big"),
            digestmod=hashlib.sha1
        ).digest()

        offset = hmac_hash[-1] & 0xF
        code = ((hmac_hash[offset] & 0x7F) << 24 |
                (hmac_hash[offset + 1] & 0xFF) << 16 |
                (hmac_hash[offset + 2] & 0xFF) << 8 |
                (hmac_hash[offset + 3] & 0xFF))

        return str(code % 10 ** 6).zfill(6)
    except (requests.exceptions.RequestException, ValueError):
        return "000000"


def get_access_token(current_token):
    if current_token == "main":
        refresh_token = const.SPOTIFY_REFRESH_TOKEN
        client_id = const.SPOTIFY_CLIENT_ID
        client_secret = const.SPOTIFY_CLIENT_SECRET
    else:
        refresh_token = const.SPOTIFY_FALLBACK_REFRESH_TOKEN
        client_id = const.SPOTIFY_FALLBACK_CLIENT_ID
        client_secret = const.SPOTIFY_FALLBACK_CLIENT_SECRET
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


def get_account_bearer() -> (str, int) or None:
    try:
        result = {"token": None, "expires": None}
        done_event = threading.Event()

        def callback(response):
            if response.url.startswith("https://open.spotify.com/api/token?"):
                if response.status == 200:
                    json_data = response.json()
                    result["token"] = json_data.get("accessToken")
                    result["expires"] = json_data.get("accessTokenExpirationTimestampMs") / 1000
                    done_event.set()
                else:
                    print(f"failed to get account bearer: {response.status} {response.text()}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies([{
                "name": "sp_dc",
                "value": const.SPOTIFY_ACCOUNT_DC,
                "domain": ".spotify.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax"
            }])
            page = context.new_page()
            page.on("response", callback)
            page.goto("https://open.spotify.com/intl-de/")

            done_event.wait(timeout=10)
            browser.close()

        if result["token"] and result["expires"]:
            return result["token"], result["expires"]
        return None, 0
    except Exception as e:
        print(f"Error getting account bearer: {e}")
        return None, 0


def update_lyrics(track_id, retried=False) -> Lyrics | None:
    global account_bearer, account_bearer_expires
    if account_bearer_expires < time.time():
        account_bearer, account_bearer_expires = get_account_bearer()

    try:
        req = requests.get(
            f"https://spclient.wg.spotify.com/color-lyrics/v2/track/{track_id}",
            headers={
                "Authorization": f"Bearer {account_bearer}",
                "app-platform": "WebPlayer",
                'spotify-app-version': '1.2.60.334.g09ff0619',
                "User-Agent": ""
            },
            params={
                "format": "json",
                "vocalRemoval": "false"
            }
        )
        if req.status_code in (401, 403) and not retried:
            account_bearer, account_bearer_expires = get_account_bearer()
            return update_lyrics(track_id, retried=True)
        json_data = req.json()
    except (requests.exceptions.RequestException, JSONDecodeError):
        return None
    if req.status_code != 200:
        return None
    lyric_data = json_data.get("lyrics")
    if not lyric_data:
        return None
    is_synced = lyric_data.get("syncType") == "LINE_SYNCED"
    if not is_synced:
        return None
    line_data = lyric_data.get("lines")
    lines = {0: "♪"}
    for line in line_data:
        words = line["words"]
        if words != "♪":
            words = "♪ " + words
        # words = helpers.smart_split(words, 50)
        lines[int(line["startTimeMs"]) / 1000] = words

    lyrics = Lyrics(lines)

    return lyrics


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


def event_reader(start, skip_rest=False):
    yield start
    yield last_event
    if skip_rest:
        return

    event_queue = queue.Queue(maxsize=10)

    with queue_lock:
        shared_event_queues.add(event_queue)

    try:
        while True:
            try:
                with Timeout(10):  # check for new events every 10 seconds
                    event = event_queue.get()
                    if event is None:
                        break
                    yield event
            except Timeout:
                yield ""  # keep alive
                continue
    except GeneratorExit:  # client disconnected
        pass
    finally:
        with queue_lock:
            shared_event_queues.discard(event_queue)


def event_writer(event):
    with queue_lock:
        dead_queues = []

        for q in shared_event_queues:
            try:
                q.put_nowait(event)
            except queue.Full:
                dead_queues.append(q)
            except Exception:
                dead_queues.append(q)

        # clean up
        for q in dead_queues:
            shared_event_queues.discard(q)


def fetch_spotify_preview(last_track_id: str) -> str | None:
    try:
        req = requests.get(f"https://open.spotify.com/embed/track/{last_track_id}")
        if req.status_code != 200:
            return None
        bs = bs4.BeautifulSoup(req.text, "html.parser")
        data = bs.find("script", {"id": "__NEXT_DATA__"}).string
        data = json.loads(data)
        return data["props"]["pageProps"]["state"]["data"]["entity"]["audioPreview"]["url"]
    except (requests.exceptions.RequestException, JSONDecodeError, KeyError):
        return None


def spotify_status_updater():
    global access_token, expires_on, last_event, current_token, current_lyrics, account_bearer, account_bearer_expires
    last_state = None
    last_track_id = None
    last_push = 0
    while True:
        if expires_on < time.time():
            access_token, expires_on = get_access_token(current_token)

        try:
            status = get_spotify_status(access_token)
            retry_after = 3
            if status and status.get("error", {}).get("status") == 429:
                retry_after = int(status.get("error", {}).get("retry_after", 3))
                if retry_after < 3:
                    retry_after = 3
                if retry_after > 1000:
                    print("We are being rate limited for too long, using fallback")
                    if current_token == "main":
                        current_token = "fallback"
                    else:
                        current_token = "main"
                    access_token, expires_on = get_access_token(current_token)
                    continue

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
            track_id = status["item"]["id"]
            if track_id != last_track_id:
                current_lyrics = None
            artist = ", ".join([artist["name"] for artist in status["item"]["artists"]])
            # get the first image that is at least 100x100
            covers = status["item"]["album"]["images"]
            cover = covers[0]["url"]  # default to the first image
            for cover_ in covers:
                if cover_["height"] >= 100 and cover_["width"] >= 100:
                    cover = cover_["url"]
            cover = cover.replace("https://i.scdn.co/image/", "/spotify-image-proxy/")
            progress_float = status["progress_ms"] / 1000
            progress = int(progress_float)
            duration_float = status["item"]["duration_ms"] / 1000
            duration = int(duration_float)
            song_url = status["item"]["external_urls"]["spotify"]
            is_playing = status["is_playing"]
            delta = duration - progress
            duration_str = f"{duration // 60}:{duration % 60:02d}"

            state = (song_title, artist, cover, duration, is_playing)
            if state == last_state and 0 <= progress - last_push <= 5:
                if not is_playing:
                    time.sleep(1.5)
                    continue
                time.sleep(0.5)
                continue
            last_state = state
            last_push = progress

            song_title = css_escape(song_title)
            artist = css_escape(artist)

            unique_id = str(time.time()).replace(".", "")
            seconds_keyframes = []
            minutes_keyframes = []
            for i in range(11):
                tmp_i = i
                if not is_playing:
                    tmp_i = 0
                if progress + tmp_i >= duration:
                    tmp_i = duration - progress
                seconds_keyframes.append(
                    f"{i * 10}% {{ counter-increment: seconds{unique_id} {(progress + tmp_i) % 60}; }}")  # noqa
                minutes_keyframes.append(
                    f"{i * 10}% {{ counter-increment: minutes{unique_id} {(progress + tmp_i) // 60}; }}")  # noqa
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

            if last_track_id == track_id:
                data += build_lyrics_css(current_lyrics, progress_float, duration_float, is_playing)

            data += "</style>"

            event_writer(data)
            if last_track_id != track_id:
                last_track_id = track_id
                current_lyrics = update_lyrics(last_track_id)
                new_lyrics_css = build_lyrics_css(current_lyrics, progress_float, duration_float, is_playing)
                new_lyrics_css = "<style>" + new_lyrics_css + "</style>"
                event_writer(new_lyrics_css)
                last_event += new_lyrics_css

            last_event = data
        except BaseException:
            traceback.print_exc()
            pass
        time.sleep(1.5)


access_token, expires_on = get_access_token("main")
account_bearer, account_bearer_expires = None, 0
current_token: Literal["main", "fallback"] = "main"
last_event = ""
current_lyrics: Lyrics | None = None
