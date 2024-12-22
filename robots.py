import flask.wrappers
from flask import make_response
from functools import wraps

import const

__all__ = ["noarchive", "index", "follow", "noindex", "nofollow", "robot_friendly"]


def get_resp(resp) -> flask.wrappers.Response:
    if not isinstance(resp, flask.wrappers.Response):
        return make_response(resp)
    return resp


def add_to_robot_tag(resp: flask.wrappers.Response, tag: str):
    if "X-Robots-Tag" in resp.headers:
        resp.headers["X-Robots-Tag"] += f", {tag}"
    else:
        resp.headers["X-Robots-Tag"] = tag


def robot_decorator(tag: str):
    def decorator(f):
        @wraps(f)
        def robot_wrapper(*args, **kwargs):
            resp = get_resp(f(*args, **kwargs))
            add_to_robot_tag(resp, tag)
            return resp
        return robot_wrapper
    return decorator


def noarchive(f):
    return robot_decorator("noarchive")(f)


def index(f):
    return robot_decorator("index")(f)


def follow(f):
    return robot_decorator("follow")(f)


def noindex(f):
    return robot_decorator("noindex")(f)


def disallow(f):
    do_not_index.append(f.__name__)
    return f


def nofollow(f):
    return robot_decorator("nofollow")(f)


def robot_friendly(app: flask.app.Flask, blogs, extra_sitemaps=None):
    if extra_sitemaps is None:
        extra_sitemaps = []
    sitemaps = [
        "sitemap.xml",
        "sitemap.txt",
        *extra_sitemaps
    ]
    sitemap_urls = gen_urllist(app, blogs)
    robots_txt = gen_robots_txt(sitemaps, app)
    site_map_txt = "\n".join([const.URL_BASE + url for url in sitemap_urls])

    @app.route("/robots.txt")
    def robots_txt_route():
        return flask.Response(robots_txt, mimetype="text/plain")

    @app.route("/sitemap.txt")
    def sitemap_txt():
        return flask.Response(site_map_txt, mimetype="text/plain")

    @app.route("/sitemap.xml")
    def sitemap_xml_route():
        return flask.Response(
            flask.render_template("sitemap.xml", urls=sitemap_urls, url_base=const.URL_BASE),
            mimetype="text/xml"
        )


def gen_robots_txt(sitemaps: [str], app: flask.app.Flask):
    # Initialize the lines for the robots.txt content
    lines = ["User-agent: *"]

    # Add Disallow lines for blocked routes
    blocked_routes = [route.rule for route in app.url_map.iter_rules() if route.endpoint in do_not_index]
    if blocked_routes:
        lines.extend([
            f"Disallow: {route} \n"
            f"Disallow: {route}?\n"
            f"Disallow: {route}/\n"
            for route in blocked_routes
        ])

    # Add Sitemap lines
    lines.extend([f"Sitemap: {const.URL_BASE}/{url}" for url in sitemaps])

    return " \n".join(lines)


def gen_urllist(app, blogs):
    # Generate URL list by checking for GET method routes and no arguments
    urls = [
        rule.rule for rule in app.url_map.iter_rules()
        if "GET" in rule.methods and not rule.arguments
    ]

    # Add blog URLs
    urls.extend([f"/blog/{blog.url_name}" for blog in blogs])

    return urls


do_not_index = []
