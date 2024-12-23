import json
import os
import random
from functools import lru_cache
from hashlib import sha256
from threading import Thread

import requests
from flask import Flask, render_template, Response, send_from_directory, request, redirect, make_response
import time
import dotenv
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

import blog
import const
import jammingen
import robots
from blog import get_blog_posts
from dino import dino_game
from helpers import get_discord_status, get_discord_invite, get_age, show_notification, \
    event_reader, spotify_status_updater, format_iso_date, get_handlers

for handler in get_handlers():
    logging.getLogger().addHandler(handler)

app = Flask(__name__, template_folder='pages')
if os.getenv("FLASK_DEBUG") != "1":
    app.wsgi_app = ProxyFix(app.wsgi_app)
dotenv.load_dotenv()


@app.route('/')
@robots.index
@robots.follow
def index():
    if "curl" in str(request.headers.get("User-Agent")).lower():
        # If the user agent is curl, return the silly dino game
        return app.response_class(dino_game(), mimetype='text/plain')

    last_blog = show_notification(blogs, request)

    theme = "pink" if random.randint(1, 20) == 1 else "blue"
    return render_template(
        'index.html',
        discord_status=discord_status,
        discord_invite=discord_invite,
        age=get_age(),
        theme=theme,
        blog=last_blog,
        is_tor=request.headers.get("Host", "").endswith(".onion"),
        const=const
    )


@app.route('/discord_status')
@robots.noindex
def discord_status_route():
    refresh_every = request.args.get("refresh_every", 10)
    return render_template("discord_status.html", discord_status=discord_status, refresh_every=refresh_every)


@app.route('/blog/')
@robots.noarchive
@robots.index
@robots.follow
def blogs_page():
    return render_template('blogs.html', blogs=blogs)


@app.route('/blog/<blog_id>')
@robots.noarchive
@robots.index
@robots.follow
def blog_post(blog_id):
    for i, blog_ in enumerate(blogs):
        if blog_.url_name == blog_id:
            date_text = format_iso_date(blog_.date)
            resp = app.make_response(render_template('blog_page.html', blog=blog_, date_text=date_text))
            if i == 0:
                resp.set_cookie("last_read", blog_.url_name, max_age=60 * 60 * 24 * 365)
            return resp

    return "Not found", 404


@app.route('/-<blog_id>')
@robots.follow
def blog_post_short(blog_id):
    for post in blogs:
        if post.hash == blog_id:
            return redirect(f"/blog/{post.url_name}", code=301)
    return "Not found", 404


@app.route('/blog/rss')
@app.route('/blog/rss.xml')
def rss():
    return Response(blog.get_rss(), mimetype="text/xml")


@app.route('/notification')
@robots.noindex
def notification():
    newest_blog = show_notification(blogs, request)
    return render_template("notification.html", blog=newest_blog)


@app.route("/email.svg")
@robots.noindex
@robots.disallow
def email_svg():
    return Response(render_template("email.svg"), mimetype="image/svg+xml")


@app.route('/listening_to')
@robots.noindex
def listening_to():
    resp = render_template("listening_to.html")
    return event_reader(resp), 200, {
        "Cache-Control": "no-cache",
        "Content-Type": "text/html; charset=utf-8",
        "X-Content-Type-Options": "nosniff",
        "Refresh": "60"
    }


@app.route('/mark_as_read', methods=["POST"])
@robots.noindex
def mark_as_read():
    url_name = request.form.get("url_name")
    if url_name is not None:
        resp = app.make_response(render_template("nothing.html"))
        resp.set_cookie("last_read", url_name, max_age=60 * 60 * 24 * 365)
        return resp
    return "Invalid request", 400


@app.route('/pgp')
def pgp():
    resp = Response(open('pgp', 'rb').read())
    resp.headers["Content-Disposition"] = "attachment; filename=damcraft_public.asc"
    return resp


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(".", "favicon.ico")


@app.route('/assets/<path:filename>')
def banner(filename):
    resp = make_response(send_from_directory("assets", filename))
    if os.getenv("FLASK_DEBUG") != "1":
        resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp


@app.route('/assets/88x31/jammin.webp')
def jammin():
    return jammingen.render()


@app.route('/.well-known/security.txt')
def security_txt():
    return send_from_directory(".", "security.txt")


@app.route('/.well-known/button')
def button():
    if not request.args.get("format") == "json":
        return send_from_directory("assets/88x31", "dam.gif")
    return Response(json.dumps([{
        "id": "damcraft.de",
        "uri": "https://damcraft.de/assets/88x31/dam.gif",
        "link": "https://damcraft.de",
        "sha256": sha256(open("assets/88x31/dam.gif", "rb").read()).hexdigest()
    }], indent=4), mimetype="application/json")


@app.route('/.well-known/atproto-did')
def atproto_did():
    return Response(const.ATPROTO_DID, mimetype="text/plain")


@app.route('/.well-known/matrix/client')
def matrix_client():
    return {
        "m.server": {
            "base_url": const.MATRIX_SERVER_BASE_URL
        },
        "m.homeserver": {
            "base_url": const.MATRIX_SERVER_BASE_URL
        },
        "org.matrix.msc3575.proxy": {
            "url": const.MATRIX_SERVER_BASE_URL
        }
    }


@app.route('/.well-known/matrix/server')
def matrix_server():
    return {
        "m.server": const.MATRIX_SERVER
    }


@app.route('/headers', methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
@robots.noindex
def parrot():
    return Response(str(request.headers), mimetype="text/plain")


@app.route('/spotify-image-proxy/<image_id>')
@lru_cache(maxsize=10)
@robots.noindex
@robots.disallow
def spotify_image_proxy(image_id):
    req = requests.get(f"https://i.scdn.co/image/{image_id}")
    resp = make_response(req.content)
    resp.headers["Content-Type"] = req.headers["Content-Type"]
    resp.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24}"
    return resp


@app.before_request
def before_request():
    # Redirect to HTTPS
    if (request.headers.get("X-Forwarded-Proto") == "http" and
            request.headers.get("Host") == "damcraft.de" and
            "curl" not in str(request.headers.get("User-Agent")).lower()):
        return redirect("https://damcraft.de" + request.path, code=301)


# Add the Onion-Location header to the response
@app.after_request
def after_request(response):
    response.headers["Onion-Location"] = "http://" + const.TOR_HOSTNAME + request.path  # noqa
    if not str(response.status_code).startswith("3"):
        response.headers["Link"] = f'<{const.URL_BASE}{request.path}>; rel="canonical"'
    response.headers["Content-Security-Policy"] = (
        f"script-src 'none'; "
        f"style-src 'self' *.{request.host} 'unsafe-inline'; "
        f"default-src 'self' *.{request.host};"
    )
    return response


discord_status = ""
discord_invite = None
blogs = get_blog_posts()


def stats_updater():
    global discord_status, discord_invite
    while True:
        discord_status = get_discord_status()
        discord_invite = get_discord_invite()

        time.sleep(10)


robots.robot_friendly(app, blogs, extra_sitemaps=["blog/rss.xml"])


# Check if Flask is in debug mode
if os.environ.get("FLASK_DEBUG") != "1":
    Thread(target=spotify_status_updater).start()
    Thread(target=stats_updater).start()
