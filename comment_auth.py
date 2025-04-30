import base64
import re
import time
from dataclasses import dataclass

import jwt
import requests
import urllib.parse

from flask import request, redirect

import const


def get_gh_oauth_url(return_url=None):
    redirect_url = const.URL_BASE + "/github/callback"
    # redirect_url = "https://localpc.damcraft.de/github/callback"
    if return_url is not None:
        redirect_url += "?return=" + urllib.parse.quote(return_url)

    base_url = (
            "https://github.com/login/oauth/authorize?scope=read:user"
            "&client_id=" + const.GITHUB_CLIENT_ID +
            "&redirect_uri=" + urllib.parse.quote(redirect_url)
    )
    return base_url


def get_gh_access_token(code):
    data = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": const.GITHUB_CLIENT_ID,
            "client_secret": const.GITHUB_CLIENT_SECRET,
            "code": code,
        },
    )
    if data.status_code != 200:
        return None
    return data.json().get("access_token")


def get_gh_user_data(token):
    data = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": "token " + token},
    )
    return data.json()


def handle_gh_callback():
    code = request.args.get("code")
    if code is None:
        return "No code provided", 400
    token = get_gh_access_token(code)
    if token is None:
        return "Invalid code or exchange failed", 400
    user_data = get_gh_user_data(token)
    if user_data is None:
        return "Failed to get user data", 500
    user_name = user_data.get("login")
    user_id = user_data.get("id")
    if user_name is None or user_id is None:
        return "Incomplete user data", 500

    signed_jwt = jwt.encode(
        {
            "user_id": user_id,
            "user_name": user_name,
            "platform": "github",
            "profile_picture": None,
            "iat": int(time.time()),
            "exp": int(time.time()) + 60 * 60 * 24 * 7
        },
        const.JWT_SECRET,
        algorithm="HS256"
    )
    redirect_path = request.args.get("return")
    if not redirect_path or not redirect_path.startswith("/"):
        redirect_path = "/"
    resp = redirect(redirect_path)
    resp.set_cookie("account_jwt", signed_jwt, max_age=60 * 60 * 24 * 7, httponly=True, secure=True, samesite="Lax")
    return resp


def get_discord_oauth_url(return_url=None):
    redirect_url = const.URL_BASE + "/discord/callback"
    # redirect_url = "https://localpc.damcraft.de/discord/callback"
    state = ""
    if return_url is not None:
        state = base64.b64encode(return_url.encode()).decode()

    base_url = (
        "https://discord.com/api/oauth2/authorize?client_id=" + const.DISCORD_CLIENT_ID +
        "&redirect_uri=" + urllib.parse.quote(redirect_url) +
        "&response_type=code&scope=identify" +
        ("&state=" + state if state else "")
    )
    return base_url


def get_discord_access_token(code):
    data = requests.post(
        "https://discord.com/api/v10/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": const.URL_BASE + "/discord/callback",
            # "redirect_uri": "https://localpc.damcraft.de/discord/callback"
        },
        auth=(const.DISCORD_CLIENT_ID, const.DISCORD_CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if data.status_code != 200:
        return None
    return data.json().get("access_token")


def get_discord_user_data(token):
    data = requests.get(
        "https://discord.com/api/v10/users/@me",
        headers={"Authorization": "Bearer " + token},
    )
    return data.json()


def handle_discord_callback():
    code = request.args.get("code")
    if code is None:
        return "No code provided", 400
    token = get_discord_access_token(code)
    if token is None:
        return "Invalid code or exchange failed", 400
    user_data = get_discord_user_data(token)
    if user_data is None:
        return "Failed to get user data", 500
    user_name = user_data.get("username")
    user_id = user_data.get("id")
    if user_name is None or user_id is None:
        return "Incomplete user data", 500
    profile_picture = user_data.get("avatar")

    signed_jwt = jwt.encode(
        {
            "user_id": user_id,
            "user_name": user_name,
            "platform": "discord",
            "profile_picture": profile_picture,
            "iat": int(time.time()),
            "exp": int(time.time()) + 60 * 60 * 24 * 7
        },
        const.JWT_SECRET,
        algorithm="HS256"
    )

    redirect_path = request.args.get("state")
    redirect_path = base64.b64decode(urllib.parse.unquote(redirect_path)).decode() if redirect_path else None
    if not redirect_path or not redirect_path.startswith("/"):
        redirect_path = "/"
    resp = redirect(redirect_path)
    resp.set_cookie("account_jwt", signed_jwt, max_age=60 * 60 * 24 * 7, httponly=True, secure=True, samesite="Lax")
    return resp


def get_mastodon_oauth_url(instance, return_url):
    try:
        # assert the instance is a valid domain
        assert re.match(
            r"^(?!-)(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$",
            instance
        ), "Invalid domain"

        if instance not in mastodon_application_cache:
            authorization_url = f"https://{instance}/oauth/authorize"
            token_url = f"https://{instance}/oauth/token"
            scope = "read:accounts profile"
            try:
                req = requests.get(f"https://{instance}/.well-known/oauth-authorization-server", timeout=3)
                if req.status_code == 200:
                    data = req.json()
                    allowed_scopes = data.get("scopes_supported", [])
                    if "profile" in allowed_scopes:
                        scope = "profile"
                    if "read:accounts" in allowed_scopes:
                        scope = "read:accounts"
                    authorization_url = data.get("authorization_endpoint", authorization_url)
                    token_url = data.get("token_endpoint", token_url)

            except requests.RequestException:
                pass
            req = requests.post(
                f"https://{instance}/api/v1/apps",
                data={
                    "client_name": "dam's blog",
                    "redirect_uris": const.URL_BASE + "/mastodon/callback/" + instance,
                    # "redirect_uris": "https://localpc.damcraft.de/mastodon/callback/" + instance,
                    "scopes": scope
                },
            ).json()
            client_id, client_secret = req["client_id"], req["client_secret"]
            mastodon_application_cache[instance] = (client_id, client_secret, authorization_url, token_url, scope)
        client_id, client_secret, authorization_url, token_url, scope = mastodon_application_cache[instance]
        redirect_url = const.URL_BASE + "/mastodon/callback/" + instance
        # redirect_url = "https://localpc.damcraft.de/mastodon/callback/" + instance
        state = ""
        if return_url is not None:
            state = base64.b64encode(return_url.encode()).decode()
        base_url = (
            f"{authorization_url}?response_type=code"
            "&client_id=" + client_id +
            "&redirect_uri=" + urllib.parse.quote(redirect_url) +
            "&scope=" + scope +
            ("&state=" + state if state else "")
        )
        return base_url
    except (requests.RequestException, KeyError, AssertionError):
        return ("/mastodon/instance_not_found?instance=" + urllib.parse.quote(instance) +
                ("&return=" + urllib.parse.quote(return_url) if return_url else ""))


def get_mastodon_access_token(instance, code):
    try:
        client_id, client_secret, authorization_url, token_url, scope = mastodon_application_cache[instance]
        data = requests.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": const.URL_BASE + "/mastodon/callback/" + instance,
                # "redirect_uri": "https://localpc.damcraft.de/mastodon/callback/" + instance,
                "client_id": client_id,
                "client_secret": client_secret,
            }
        )
        if data.status_code != 200:
            return None
        return data.json().get("access_token")
    except (requests.RequestException, KeyError):
        return None


def get_mastodon_user_data(instance, token):
    try:
        data = requests.get(
            f"https://{instance}/api/v1/accounts/verify_credentials",
            headers={"Authorization": "Bearer " + token},
        )
        if data.status_code != 200:
            return None
        return data.json()
    except requests.RequestException:
        return None


def handle_mastodon_callback(instance):
    code = request.args.get("code")
    if code is None:
        return "No code provided", 400
    token = get_mastodon_access_token(instance, code)
    if token is None:
        return "Invalid code or exchange failed", 400
    user_data = get_mastodon_user_data(instance, token)
    if user_data is None:
        return "Failed to get user data", 500
    user_name = user_data.get("username")
    account = "@" + user_data.get("acct") + "@" + instance
    url = user_data.get("url")
    if user_name is None or account is None:
        return "Incomplete user data", 500
    if url is None or not url.startswith("https://"):
        url = "https://" + instance + "/@" + user_name
    profile_picture = user_data.get("avatar")
    if not profile_picture:
        profile_picture = "/assets/mastodon.png"

    signed_jwt = jwt.encode(
        {
            "user_id": account,
            "user_name": user_name,
            "platform": "mastodon",
            "profile_picture": profile_picture,
            "profile_url": url,
            "iat": int(time.time()),
            "exp": int(time.time()) + 60 * 60 * 24 * 7
        },
        const.JWT_SECRET,
        algorithm="HS256"
    )
    redirect_path = request.args.get("state")
    redirect_path = base64.b64decode(urllib.parse.unquote(redirect_path)).decode() if redirect_path else None
    if not redirect_path or not redirect_path.startswith("/"):
        redirect_path = "/"
    resp = redirect(redirect_path)
    resp.set_cookie("account_jwt", signed_jwt, max_age=60 * 60 * 24 * 7, httponly=True, secure=True, samesite="Lax")
    return resp


def get_reddit_oauth_url(return_url=None):
    redirect_url = const.URL_BASE + "/reddit/callback"
    # redirect_url = "https://localpc.damcraft.de/reddit/callback"
    state = ""
    if return_url is not None:
        state = base64.b64encode(return_url.encode()).decode()

    base_url = (
        "https://www.reddit.com/api/v1/authorize?client_id=" + const.REDDIT_CLIENT_ID +
        "&scope=identity" +
        "&redirect_uri=" + urllib.parse.quote(redirect_url) +
        "&response_type=code" +
        ("&state=" + state if state else "")
    )
    return base_url


def get_reddit_access_token(code):
    data = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": const.URL_BASE + "/reddit/callback",
            # "redirect_uri": "https://localpc.damcraft.de/reddit/callback"
        },
        auth=(const.REDDIT_CLIENT_ID, const.REDDIT_CLIENT_SECRET),
        headers={"User-Agent": "dam's blog"},
    )
    if data.status_code != 200:
        return None
    return data.json().get("access_token")


def get_reddit_user_data(token):
    try:
        data = requests.get(
            "https://oauth.reddit.com/api/v1/me",
            headers={"Authorization": "Bearer " + token}
        )
        if data.status_code != 200:
            return None
        return data.json()
    except requests.RequestException:
        return None


def handle_reddit_callback():
    code = request.args.get("code")
    if code is None:
        return "No code provided", 400
    token = get_reddit_access_token(code)
    if token is None:
        return "Invalid code or exchange failed", 400
    user_data = get_reddit_user_data(token)

    if user_data is None:
        return "Failed to get user data", 500
    user_name = user_data.get("name")
    user_id = user_data.get("subreddit", {}).get("display_name_prefixed")

    if user_name is None or user_id is None:
        return "Incomplete user data", 500

    signed_jwt = jwt.encode(
        {
            "user_id": user_id,
            "user_name": user_name,
            "platform": "reddit",
            "iat": int(time.time()),
            "exp": int(time.time()) + 60 * 60 * 24 * 7
        },
        const.JWT_SECRET,
        algorithm="HS256"
    )
    redirect_path = request.args.get("state")
    redirect_path = base64.b64decode(urllib.parse.unquote(redirect_path)).decode() if redirect_path else None
    if not redirect_path or not redirect_path.startswith("/"):
        redirect_path = "/"
    resp = redirect(redirect_path)
    resp.set_cookie("account_jwt", signed_jwt, max_age=60 * 60 * 24 * 7, httponly=True, secure=True, samesite="Lax")
    return resp


def is_logged_in(request_):
    return get_user_data_from_request(request_) is not None


def get_user_data_from_request(request_):
    jwt_cookie = request_.cookies.get("account_jwt")
    if jwt_cookie is None:
        return None
    try:
        data = jwt.decode(jwt_cookie, const.JWT_SECRET, algorithms=["HS256"])
        return UserData(data["user_id"], data["user_name"], data["platform"], data.get("profile_picture"), data.get("profile_url"))
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@dataclass
class UserData:
    user_id: int
    user_name: str
    platform: str
    profile_picture: str | None = None
    profile_url: str | None = None


mastodon_application_cache = {}
