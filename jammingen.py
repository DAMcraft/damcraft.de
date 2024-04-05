import os
import time
from hashlib import sha256

from user_agents import parse
from PIL import Image, ImageDraw, WebPImagePlugin
from flask import Response, request, redirect
import requests


def get_ip_info(ip: str):
    req = requests.get(f"https://ipinfo.io/{ip}?token={os.environ.get('IPINFO_API_KEY')}")
    return req.json()


def render():
    if not os.path.exists("cache"):
        os.mkdir("cache")

    ip = request.headers.get("X-Client-IP") or request.remote_addr
    if ip == "127.0.0.1":
        return b""
    if ":" in ip:
        return redirect("https://4.damcraft.de" + request.path, code=302)

    # Parse the useragent
    useragent = request.headers.get("User-Agent")
    ua_hash = sha256(useragent.encode()).hexdigest()[:8]
    if useragent is not None:
        useragent = parse(useragent)

    # Delete all files older than 1 hour
    for file in os.listdir("cache"):
        if os.path.getmtime(f"cache/{file}") < time.time() - 60 * 60:
            os.remove(f"cache/{file}")

    if os.path.exists(f"cache/{ip}_{ua_hash}.webp"):
        return Response(open(f"cache/{ip}_{ua_hash}.webp", "rb"), mimetype="image/webp")

    data = get_ip_info(ip)

    # Open the animated image
    jamming: WebPImagePlugin.WebPImageFile = Image.open("88x31/jammin.webp")  # type: ignore

    texts = [
        "IP: " + ip,
        "Browser: " + useragent.browser.family,
        "OS: " + useragent.os.family,
        "Country: " + data["country"],
        data["region"],
        data["city"],
        "ISP: " + data["org"].split(" ")[1],
        "Lat: " + data["loc"].split(",")[0],
        "Lon: " + data["loc"].split(",")[1],
        "Postal: " + data["postal"],
        "Timezone: " + data["timezone"].split("/")[1],
    ]

    # Strip out special characters
    for i, text in enumerate(texts):
        texts[i] = "".join([c for c in text if ord(c) < 256])

    frames = []
    current_text = []

    # Go through each frame and add the text
    for i in range(jamming.n_frames):
        jamming.seek(i)
        frame = jamming.copy()
        draw = ImageDraw.Draw(frame)

        ti = i - 133
        if ti >= 0:
            if ti % 10 == 0:
                if ti // 10 < len(texts):
                    current_text.append(texts[ti // 10])
                if len(current_text) > 3:
                    current_text.pop(0)

            for j, text in enumerate(current_text):
                draw.text((0, j * 10), text, fill="white")

        frames.append(frame)
    # Save the new image to /cache/[ip].webp
    frames[0].save(
        f"cache/{ip}_{ua_hash}.webp", save_all=True, append_images=frames[1:], duration=jamming.info["duration"], loop=0
    )

    # Return the image
    return Response(open(f"cache/{ip}_{ua_hash}.webp", "rb"), mimetype="image/webp")
