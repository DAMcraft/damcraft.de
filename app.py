import datetime
import json
import os
import random
import urllib.parse
from hashlib import sha256
from threading import Thread

import pytz
import requests
from flask import Flask, render_template, Response, send_from_directory, request, redirect, make_response
from functools import lru_cache
import time
import dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

import blog
import const
import cors
import comment_auth
import jammingen
import robots
from blog import get_blog_posts
from dino import dino_game
from helpers import get_discord_status, get_discord_invite, get_age, show_notification, \
    format_iso_date, fishlogic, random_copyright_year, get_server_status
from spotify import spotify_status_updater, event_reader

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

    # theme = "pink" if random.randint(1, 20) == 1 else "blue"

    tz_string = "Europe/Berlin"
    tz = pytz.timezone(tz_string)
    now = datetime.datetime.now(tz)
    midnight = tz.localize(datetime.datetime(now.year, now.month, now.day, 0, 0, 0))
    return render_template(
        'index.html',
        discord_status=discord_status,
        discord_invite_url=discord_invite,
        discord_server_info=discord_server_info,
        age=get_age(),
        # theme=theme,
        blog=last_blog,
        is_tor=request.headers.get("Host", "").endswith(".onion"),
        const=const,
        style_hash=style_hash,
        pgp_key=pgp_key.decode("utf-8"),
        day_seconds=int(now.timestamp() - midnight.timestamp()),
        tz=tz_string,
    )


@app.route('/discord_status')
@robots.noindex
def discord_status_route():
    refresh_every = request.args.get("refresh_every", 10)
    return render_template("discord_status.html", discord_status=discord_status, refresh_every=refresh_every)


@app.route('/blogs/')
@app.route('/blogs/<language>')
@robots.noarchive
@robots.index
@robots.follow
def blogs_page(language=None):
    if language == "en":
        return redirect("/blogs/", code=301)
    language = language or "en"
    if language not in blogs.languages:
        return "Language not found", 404
    return render_template(
        'blogs_list.html',
        blogs=blogs.get_by_language(language),
        copyright=random_copyright_year(),
        lang=language,
        all_languages=blogs.languages,
        style_hash=blog_style_hash,
    )


@app.route('/blog/')
@app.route('/blog/<url_name>')
@robots.noarchive
@robots.index
@robots.follow
def blog_post(url_name=None):
    if url_name is None:
        return redirect("/blogs/", code=301)
    blog_ = blogs.get_by_url_name(urllib.parse.unquote(url_name))
    if not blog_:
        return "Blog post not found", 404

    user_data = comment_auth.get_user_data_from_request(request)

    date_text = format_iso_date(blog_.date)
    resp = app.make_response(
        render_template(
            'blog_post.html',
            blog=blog_,
            date_text=date_text,
            user_data=user_data,
            copyright=random_copyright_year(),
            style_hash=blog_style_hash
        )
    )
    if (blog_.original_url or blog_.url_name) == blogs.get_by_language("en")[0].url_name:
        resp.set_cookie(
            "last_read",
            (blog_.original_url or blog_.url_name),
            max_age=60 * 60 * 24 * 365,
            samesite="Lax", secure=True, httponly=True)
    links = []
    for language, url_name in blog_.get_languages().items():
        links.append(f'<{const.URL_BASE}/blog/{url_name}>; rel="alternate"; hreflang="{language}"')
    resp.headers["Link"] = ", ".join(links)
    return resp


@app.route('/blog/<blog_id>/comment', methods=["POST"])
@robots.noindex
def comment(blog_id):
    comment_id = blog.handle_comment(blog_id, request, blogs)
    if comment_id:
        return redirect(f"/blog/{blog_id}#comment-{comment_id}")
    return redirect(f"/blog/{blog_id}#comments-section")


@app.route('/blog/<blog_id>/comments/<comment_id>', methods=["POST"])
@robots.noindex
def modify_comment(blog_id, comment_id):
    blog.modify_comment(blog_id, comment_id, request, blogs)
    return redirect(f"/blog/{blog_id}#comment-{comment_id}")


@app.route('/-<blog_hash>')
@robots.follow
def blog_post_short(blog_hash):
    post = blogs.get_by_hash(urllib.parse.unquote(blog_hash))
    if post:
        return redirect(f"/blog/{post.url_name}", code=301)
    return "Blog post not found", 404


@app.route('/blog/rss')
@app.route('/blog/rss.xml')
def rss():
    lang = request.args.get("lang", "en")
    return Response(blog.get_rss(blogs, lang), mimetype="text/xml")


@app.route('/blog/news_sitemap.xml')
def news_sitemap():
    return Response(blog.get_news_sitemap(blogs), mimetype="text/xml")


@app.route('/notification')
@robots.noindex
def notification():
    newest_blog = show_notification(blogs, request)
    return render_template("notification.html", blog=newest_blog)


@app.route("/email.svg")
@robots.noindex
@robots.disallow
def email_svg():
    return Response(
        render_template("email.svg", email=const.EMAIL),
        mimetype="image/svg+xml"
    )


@app.route('/listening_to')
@robots.noindex
def listening_to():
    refresh = request.args.get("refresh")

    resp = render_template("listening_to.html", refresh=refresh)
    if refresh:
        return event_reader(resp, skip_rest=True), 200, {
            "Cache-Control": "no-cache",
            "Content-Type": "text/html; charset=utf-8",
            "Refresh": "5; url=/listening_to"
        }

    return event_reader(resp), 200, {
        "Cache-Control": "no-cache",
        "Content-Type": "text/html; charset=utf-8"
    }


@app.route('/mark_as_read', methods=["POST"])
@robots.noindex
def mark_as_read():
    url_name = request.form.get("url_name")
    if url_name is not None:
        resp = app.make_response(send_from_directory("assets", "nothing.html"))
        resp.set_cookie("last_read", url_name, max_age=60 * 60 * 24 * 365, samesite="Lax", secure=True, httponly=True)
        return resp
    return "Invalid request", 400


@app.route('/github/callback')
def github_callback():
    return comment_auth.handle_gh_callback()


@app.route('/github/profile_image/<user_id>')
@lru_cache(maxsize=30)
@robots.noindex
@robots.disallow
def github_profile_image(user_id):
    req = requests.get(f"https://avatars.githubusercontent.com/u/{user_id}?v=4&s=100")
    resp = make_response(req.content)
    resp.headers["Content-Type"] = req.headers["Content-Type"]
    resp.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24}"
    return resp


@app.route('/github/login')
def github_login():
    return_url = request.args.get("return")
    if return_url and not return_url.startswith("/"):
        return_url = "/"
    return redirect(comment_auth.get_gh_oauth_url(return_url=return_url))


@app.route('/discord/login')
def discord_login():
    return_url = request.args.get("return")
    if return_url and not return_url.startswith("/"):
        return_url = "/"
    return redirect(comment_auth.get_discord_oauth_url(return_url=return_url))


@app.route('/discord/callback')
def discord_callback():
    return comment_auth.handle_discord_callback()


@app.route('/discord/profile_image/<user_id>/<avatar_id>')
@lru_cache(maxsize=30)
@robots.noindex
@robots.disallow
def discord_profile_image(user_id, avatar_id):
    resp = make_response(send_from_directory("assets", "discord_default.png"))
    resp.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24}"
    if avatar_id is None:
        return resp
    req = requests.get(f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}.png?size=256")
    if req.status_code == 200:
        resp = make_response(req.content)
        resp.headers["Content-Type"] = req.headers["Content-Type"]
    resp.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24}"
    return resp


@app.route('/mastodon/login', methods=["POST"])
def mastodon_login():
    instance = request.form.get("instance")
    return_url = request.args.get("return")
    if return_url and not return_url.startswith("/"):
        return_url = "/"
    return redirect(comment_auth.get_mastodon_oauth_url(instance, return_url=return_url))


@app.route('/mastodon/callback/<instance>')
def mastodon_callback(instance):
    return comment_auth.handle_mastodon_callback(instance)


@app.route('/mastodon/instance_not_found')
def instance_not_found():
    return render_template("instance_not_found.html", instance=request.args.get("instance"),
                           return_url=request.args.get("return")), 404


@app.route('/mastodon/profile_image')
@lru_cache(maxsize=30)
@robots.noindex
@robots.disallow
def mastodon_profile_image():
    # Remove the protocol from the URL
    try:
        image_url = request.args.get("url")
        image_url = image_url.removeprefix("https://").removeprefix("http://")
        req = requests.get(f"https://{image_url}")
        req.raise_for_status()
        resp = make_response(req.content)
        resp.headers["Content-Type"] = req.headers.get("Content-Type", "image/png")
    except requests.RequestException:
        resp = make_response(send_from_directory("assets", "mastodon.png"))
    resp.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24}"
    return resp


@app.route('/reddit/login')
def reddit_login():
    return_url = request.args.get("return")
    if return_url and not return_url.startswith("/"):
        return_url = "/"
    return redirect(comment_auth.get_reddit_oauth_url(return_url=return_url))


@app.route('/reddit/callback')
def reddit_callback():
    return comment_auth.handle_reddit_callback()


@app.route('/reddit/profile_image/<user_id>')
@robots.noindex
@robots.disallow
def reddit_profile_image(user_id):
    try:
        req = requests.get(f"https://www.reddit.com/user/{user_id}/about.json", headers={
            "User-Agent": "lina's blog"
        })
        if req.status_code == 200:
            data = req.json()
            if "icon_img" in data["data"]:
                icon_url = data["data"]["icon_img"]
                if icon_url:
                    req = requests.get(icon_url)
                    print(req.status_code)
                    resp = make_response(req.content)
                    resp.headers["Content-Type"] = req.headers["Content-Type"]
                    resp.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24}"
                    return resp
    except requests.RequestException:
        pass
    # If the request fails or the icon is not found, return a default image
    resp = make_response(send_from_directory("assets", "reddit_default.png"))
    return resp


@app.route("/logout", methods=["POST"])
def logout():
    # Remove the cookie from the response
    redirect_url = request.form.get("redirect")
    if not redirect_url or not redirect_url.startswith("/"):
        redirect_url = "/"
    resp = app.make_response(redirect(redirect_url))
    resp.set_cookie("account_jwt", "", expires=0, samesite="Lax", secure=True, httponly=True)
    return resp


@app.route('/pgp')
def pgp():
    resp = Response(pgp_key, mimetype="text/plain")
    resp.headers["Content-Disposition"] = "inline; filename=lina_public.asc"
    return resp


@app.route('/favicon.ico')
def favicon():
    return send_from_directory("assets", "favicon.ico")


@app.route('/assets/<path:filename>')
def banner(filename):
    resp = make_response(send_from_directory("assets", filename))
    if os.getenv("FLASK_DEBUG") != "1":
        resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp


@app.route('/assets/88x31/jammin.webp')
@robots.disallow
@robots.noindex
def jammin():
    return jammingen.render()


@app.route('/assets/88x31/makeafish.png')
@robots.disallow
@robots.noindex
def makeafish():
    return fishlogic()


@app.route('/assets/88x31/dam.gif')
def redirect_new_button():
    return redirect("/assets/88x31/lina.gif", code=301)


@app.route('/.well-known/<path:filename>')
@cors.allow_origin("*")
def security_txt(filename):
    request_host = request.headers.get("Host", "").lower()
    # check if there is well-known/{host}/{filename}, else return the default well-known/default/{filename}
    if os.path.exists(os.path.join("well-known", request_host, filename)):
        return send_from_directory(os.path.join("well-known", request_host), filename)
    return send_from_directory(os.path.join("well-known", "default"), filename)


@app.route('/.well-known/button.json')
@cors.allow_origin("*")
def button():
    return Response(json.dumps({
        "$schema": "https://codeberg.org/LunarEclipse/well-known-button/raw/branch/main/drafts/"
                   "button-2024-06.schema.json",
        "default": const.MAIN_DOMAIN,
        "buttons": [
            {
                "id": const.MAIN_DOMAIN,
                "uri": "https://lina.sh/assets/88x31/lina.gif",
                "link": "https://lina.sh/",
                "sha256": button_hash,
                "alt": "Lina / lina.sh"
            }
        ]
    }, indent=4), mimetype="application/json")


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
            request.headers.get("Host") == "lina.sh" and
            "curl" not in str(request.headers.get("User-Agent")).lower()):
        return redirect("https://lina.sh" + request.path, code=301)


@app.after_request
def after_request(response):
    response.headers["Onion-Location"] = "http://" + const.TOR_HOSTNAME + request.path  # noqa
    if not str(response.status_code).startswith("3"):
        path = urllib.parse.quote(request.path)
        query = f"?{request.query_string.decode()}" if request.query_string else ""
        canonical = f'<{const.URL_BASE}{path}{query}>; rel="canonical"'
        if response.headers.get("Link") and canonical not in response.headers["Link"]:
            response.headers["Link"] += f", {canonical}"
        else:
            response.headers["Link"] = canonical
    response.headers["Content-Security-Policy"] = (
        f"script-src 'none'; "
        f"style-src 'self' *.{request.host} 'unsafe-inline'; "
        f"img-src 'self' data:; "
        f"default-src 'self' *.{request.host};"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


discord_status = ""
discord_invite = None
discord_server_info = {}

blogs = get_blog_posts()

style_hash = sha256(open("assets/style.css", "rb").read()).hexdigest()[:8]
blog_style_hash = sha256(open("assets/blog.css", "rb").read()).hexdigest()[:8]
button_hash = sha256(open("assets/88x31/lina.gif", "rb").read()).hexdigest()
pgp_key = open('pgp', 'rb').read()


def stats_updater():
    global discord_status, discord_invite, discord_server_info
    while True:
        discord_status = get_discord_status()
        discord_invite = get_discord_invite()
        if discord_invite:
            discord_server_info = get_server_status(discord_invite)
        time.sleep(30)


robots.robot_friendly(app, blogs, extra_sitemaps=["blog/rss.xml", "blog/news_sitemap.xml"])

# Check if Flask is in debug mode
if os.environ.get("FLASK_DEBUG") != "1":
    Thread(target=spotify_status_updater, daemon=True).start()
    Thread(target=stats_updater, daemon=True).start()
