import json
import os
import random
from hashlib import sha256
from threading import Thread

from flask import Flask, render_template, Response, send_from_directory, request, redirect
import time
import dotenv

import jammingen
from dino import dino_game
from helpers import get_discord_status, get_discord_invite, get_age

# Disable werkzeug logging
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
# ------------------------

app = Flask(__name__, template_folder='pages')
dotenv.load_dotenv()


@app.route('/')
def index():
    if "curl" in str(request.headers.get("User-Agent")).lower():
        # If the user agent is curl, return the silly dino game
        return app.response_class(dino_game(), mimetype='text/plain')

    theme = "pink" if random.randint(1, 20) == 1 else "blue"
    return render_template(
        'index.html',
        discord_status=discord_status,
        discord_invite=discord_invite,
        age=get_age(),
        theme=theme,
        is_tor=request.headers.get("Host", "").endswith(".onion")
    )


@app.route('/discord_status')
def discord_status_route():
    refresh_every = request.args.get("refresh_every", 10)
    return render_template("discord_status.html", discord_status=discord_status, refresh_every=refresh_every)


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


@app.route('/.well-known/button')
def button():
    if not request.args.get("format") == "json":
        return send_from_directory("88x31", "dam.gif")
    return Response(json.dumps([{
        "id": "damcraft.de",
        "uri": "https://damcraft.de/88x31/dam.gif",
        "link": "https://damcraft.de",
        "sha256": sha256(open("88x31/dam.gif", "rb").read()).hexdigest()
    }], indent=4), mimetype="application/json")


@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(".", "robots.txt")


@app.route('/headers', methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
def parrot():
    return Response(str(request.headers), mimetype="text/plain")


@app.before_request
def before_request():
    # Redirect to HTTPS
    if (request.headers.get("X-Forwarded-Proto") == "http" and
            request.headers.get("Host") == "damcraft.de" and
            "curl" not in str(request.headers.get("User-Agent")).lower()):
        return redirect("https://damcraft.de" + request.path, code=302)


# Add the Onion-Location header to the response
@app.after_request
def after_request(response):
    response.headers["Onion-Location"] = "http://" + os.environ.get("TOR_HOSTNAME") + request.path  # noqa
    return response


discord_status = ""
discord_invite = None


def stats_updater():
    global discord_status, discord_invite
    while True:
        discord_status = get_discord_status()
        discord_invite = get_discord_invite()

        time.sleep(10)


# Check if Flask is in debug mode
if os.environ.get("FLASK_DEBUG") != "1":
    Thread(target=stats_updater).start()
