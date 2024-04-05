import os
import random
from datetime import datetime
from hashlib import sha256
from threading import Thread

from flask import Flask, render_template, Response, send_from_directory, request, redirect
import requests
import time
import dotenv

import jammingen
from dino import dino_game

# Disable werkzeug logging
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, template_folder='pages')
dotenv.load_dotenv()


@app.route('/')
def index():
    if "curl" in str(request.headers.get("User-Agent")).lower():
        return app.response_class(dino_game(), mimetype='text/plain')

    # No clue this might fuck up on some specific dates or some shit like that,
    # but I don't give enough of a shit to put more thought into it
    age = (datetime.now() - datetime(2007, 6, 24)).days // 365

    theme = "pink" if random.randint(1, 20) == 1 else "blue"
    return render_template(
        'index.html',
        discord_status=discord_status[0],
        server_count=ss_server_count[0],
        discord_info=discord_info[0],
        age=age,
        theme=theme,
        is_tor=request.headers.get("Host", "").endswith(".onion")
    )


@app.route('/discord_status')
def discord_status_route():
    status = discord_status[0]
    refresh_every = request.args.get("refresh_every", 10)
    return render_template("discord_status.html", discord_status=status, refresh_every=refresh_every)


@app.route('/pgp')
def pgp():
    resp = Response(open('pgp', 'rb').read())
    resp.headers["Content-Disposition"] = "attachment; filename=damcraft_public.asc"
    return resp


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(".", "favicon.ico")


@app.route('/88x31/<path:filename>')
def banner(filename):
    return send_from_directory("88x31", filename)


@app.route('/88x31/jammin.webp')
def jammin():
    return jammingen.render()


@app.route('/dam.png')
def damdotpng():
    return send_from_directory(".", "dam.png")


@app.route('/.well-known/security.txt')
def security_txt():
    return send_from_directory(".", "security.txt")


@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(".", "robots.txt")


@app.route("/delta_ip")
def delta_ip():
    ip = request.headers.get("X-Client-IP")
    if ":" not in ip:
        return "Only IPv6 is supported", 400
    passcode = request.args.get("passcode")
    passcode_hash = sha256(passcode.encode()).hexdigest()
    if passcode_hash != os.environ.get("DELTA_PASSCODE_HASH"):
        return "Invalid passcode", 403

    # Make the last 64 bits equal to the Pi's interface ID
    ip = ":".join(ip.split(":")[:4])
    ip += os.environ.get("DELTA_INTERFACE_ID")

    with open("delta_ip.txt", "w") as f:
        f.write(ip)

    # Update Cloudflare
    requests.patch(
        f"https://api.cloudflare.com/client/v4/zones/{os.environ.get('CLOUDFLARE_ZONE_ID')}/dns_records/"
        f"{os.environ.get('CLOUDFLARE_RECORD_ID')}",
        headers={"Authorization": f"Bearer {os.environ.get('CLOUDFLARE_API_KEY')}", "Content-Type": "application/json"},
        json={"type": "AAAA", "name": f"{os.environ.get('DELTA_HOSTNAME')}", "content": ip, "ttl": 1, "proxied": False}
    )

    return "IP set to " + ip


@app.before_request
def before_request():
    if (request.headers.get("X-Forwarded-Proto") == "http" and
            request.headers.get("Host") == "damcraft.de" and
            "curl" not in str(request.headers.get("User-Agent")).lower()):
        return redirect("https://damcraft.de" + request.path, code=302)


# Add the Onion-Location header to the response
@app.after_request
def after_request(response):
    response.headers["Onion-Location"] = "http://" + os.environ.get("TOR_HOSTNAME") + request.path
    return response


discord_status = [{}]
ss_server_count = [""]
discord_info = [{"member_count": None, "instant_invite": None}]


def stats_updater():
    global discord_status
    global ss_server_count
    i = 0
    while True:
        i += 1
        try:
            req = requests.get("https://api.lanyard.rest/v1/users/495257778802393088").json()
            discord_status[0] = (req.get("success") or "") and req.get("data", {}).get("discord_status", "")
        except:  # noqa
            discord_status[0] = {}
        try:
            server_count = requests.get("https://api.serverseeker.net/stats").json().get("server_count")
            server_count = round(server_count / 10000) * 10000
            ss_server_count[0] = f"{server_count:,}"
        except:  # noqa
            ss_server_count[0] = ""
        try:
            # Only update the member count every 10 minutes
            if i % 60 == 0:
                # Get the member count of the Discord server
                member_count = requests.get(
                    "https://discord.com/api/v9/guilds/1087081486747971705?with_counts=true",
                    headers={"Authorization": "Bot " + os.environ.get("DISCORD_TOKEN")}
                ).json().get("approximate_member_count", 0)
                widget = (requests.get(
                    "https://discord.com/api/v9/guilds/1087081486747971705/widget.json"
                ).json())
                instant_invite = widget.get("instant_invite")
                discord_info[0] = {
                    "member_count": f"{member_count:,}",
                    "instant_invite": instant_invite if instant_invite else discord_info[0].get("instant_invite")
                }
        except:  # noqa
            discord_info[0] = {
                "member_count": None,
                "instant_invite": None
            }

        time.sleep(10)


# Check if Flask is in debug mode
if os.environ.get("FLASK_DEBUG") != "1":
    Thread(target=stats_updater).start()
