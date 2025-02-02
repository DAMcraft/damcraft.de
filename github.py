import time
from dataclasses import dataclass

import jwt
import requests
import urllib.parse

from flask import request, redirect

import const


def get_oauth_url(return_url=None):
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


def get_access_token(code):
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


def get_user_data(token):
    data = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": "token " + token},
    )
    return data.json()


def handle_callback():
    code = request.args.get("code")
    if code is None:
        return "No code provided", 400
    token = get_access_token(code)
    if token is None:
        return "Invalid code or exchange failed", 400
    user_data = get_user_data(token)
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
    resp.set_cookie("github_jwt", signed_jwt, max_age=60 * 60 * 24 * 7, httponly=True, secure=True, samesite="Lax")
    return resp


def is_logged_in(request_):
    return get_user_data_from_request(request_) is not None


def get_user_data_from_request(request_):
    jwt_cookie = request_.cookies.get("github_jwt")
    if jwt_cookie is None:
        return None
    try:
        data = jwt.decode(jwt_cookie, const.JWT_SECRET, algorithms=["HS256"])
        return UserData(data["user_id"], data["user_name"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@dataclass
class UserData:
    user_id: int
    user_name: str
