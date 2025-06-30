import os
import time
from hashlib import sha256

from user_agents import parse
from PIL import Image, ImageDraw, WebPImagePlugin
from flask import Response, request, redirect
import requests

import const

# Cache duration in seconds
CACHE_DURATION = 60 * 60  # 1 hour


def get_ip_info(ip: str):
    empty = {
        "country": "",
        "region": "",
        "city": "",
        "loc": "0,0",
        "org": "AS1 TEST",
        "postal": "",
        "timezone": "UTC/UTC",
    }
    req = requests.get(f"https://ipinfo.io/{ip}?token={const.IP_INFO_API_KEY}")
    empty.update(req.json())  # Ensure that all keys are present
    return empty


def render():
    if not os.path.exists("cache"):
        os.mkdir("cache")

    ip = request.headers.get("X-Forwarded-For") or request.remote_addr
    if ip == "127.0.0.1":
        return b""
    if ":" in ip:
        return redirect("https://4.lina.sh" + request.path, code=302)

    # Parse the useragent
    useragent = request.headers.get("User-Agent")
    if useragent is None:
        return b""

    ua_hash = sha256(useragent.encode()).hexdigest()[:8]
    useragent_parsed = parse(useragent)

    # Check cache for existing image
    cache_file = f"cache/{ip}_{ua_hash}.webp"
    if os.path.exists(cache_file):
        # Check file age before serving from cache
        if os.path.getmtime(cache_file) > time.time() - CACHE_DURATION:
            return Response(open(cache_file, "rb"), mimetype="image/webp")

    # Delete files older than 1 hour
    for file in os.listdir("cache"):
        if os.path.getmtime(f"cache/{file}") < time.time() - CACHE_DURATION:
            os.remove(f"cache/{file}")

    data = get_ip_info(ip)

    # Open the animated image once and reuse it
    jamming: WebPImagePlugin.WebPImageFile = Image.open("assets/88x31/jammin.webp")  # type: ignore

    texts = [
        "IP: " + ip,
        "Browser: " + useragent_parsed.browser.family if useragent_parsed else "Unknown",
        "OS: " + useragent_parsed.os.family if useragent_parsed else "Unknown",
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
    texts = ["".join([c for c in text if ord(c) < 256]) for text in texts]
    start_processing_time = time.time()

    # Pre-render all text images at the start
    text_images = {}
    for text in texts:
        # Create a new image with a black background (same height as text)
        text_img = Image.new('RGBA', (jamming.width, 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        draw.text((0, 0), text, fill="white")
        text_images[text] = text_img

    # Pre-calculate which frames need text updates
    start_frame = 133
    text_update_frames = {start_frame + i * 10: texts[i] for i in range(len(texts))}
    current_text = []
    frames = []

    # Go through each frame and add the text
    for i in range(jamming.n_frames):
        jamming.seek(i)
        frame = jamming.copy()

        # Only process text if we're past the start frame
        if i >= start_frame:
            # Check if this frame needs a text update
            if i in text_update_frames:
                current_text.append(text_update_frames[i])
                if len(current_text) > 3:
                    current_text.pop(0)

            # Paste pre-rendered text images
            if current_text:
                for j, text in enumerate(current_text):
                    frame.paste(text_images[text], (0, j * 10), text_images[text])

        frames.append(frame)

    # Save the new image to /cache/[ip].webp
    frames[0].save(
        cache_file, save_all=True, append_images=frames[1:], duration=jamming.info["duration"], loop=0
    )

    # Return the image
    return Response(open(cache_file, "rb"), mimetype="image/webp")
