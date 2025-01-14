import time

import jwt
import requests
import urllib.parse

from flask import request, redirect

import const
import helpers
from blog import BlogPost


def get_oauth_url(return_url=None):
    # redirect_url = const.URL_BASE + "/github/callback" TODO: USE THIS
    redirect_url = "https://localpc.damcraft.de/github/callback"
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
    resp = redirect(request.args.get("return", "/"), code=302)
    resp.set_cookie("github_jwt", signed_jwt, max_age=60 * 60 * 24 * 7, httponly=True, secure=True, samesite="Lax")
    return resp


def is_logged_in(request_):
    return get_user_data_from_request(request_) is not None


def get_user_data_from_request(request_):
    jwt_cookie = request_.cookies.get("github_jwt")
    if jwt_cookie is None:
        return None
    try:
        return jwt.decode(jwt_cookie, const.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def handle_comment(blog_id, request_, blogs):
    blog: BlogPost = next((blog for blog in blogs if blog.url_name == blog_id), None)
    if not blog:
        return
    user_data = get_user_data_from_request(request_)
    if not user_data:
        return
    user_id = user_data["user_id"]
    user_name = user_data["user_name"]
    content = request_.form.get("comment")
    content = helpers.sanitize_comment(content)
    if not content:
        return
    blog.add_comment(user_name, user_id, content, int(time.time()))


def modify_comment(blog_id, comment_id, request_, blogs: [BlogPost]):
    blog: BlogPost = next((blog for blog in blogs if blog.url_name == blog_id), None)
    if not blog:
        return
    user_data = get_user_data_from_request(request_)
    if not user_data:
        return
    user_id = user_data["user_id"]

    # Get the comment to verify ownership
    comments = blog.get_comments()
    comment = next((c for c in comments if str(c.comment_id) == comment_id), None)
    if not comment:
        return

    # Verify comment ownership
    if comment.user_id != user_id:
        return
    action = request_.form.get('action')

    if action == 'edit':
        new_content = request_.form.get('content')
        new_content = helpers.sanitize_comment(new_content)
        if not new_content:
            return

        success = blog.edit_comment(comment_id, new_content)
        if not success:
            return
    elif action == 'delete':
        success = blog.delete_comment(comment_id)
        if not success:
            return
    else:
        return

    blog.mark_comments_for_update()
