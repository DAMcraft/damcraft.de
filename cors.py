import flask.wrappers
from flask import make_response, request
from functools import wraps

__all__ = ["allow_origin", "allow_credentials", "allow_methods", "allow_headers"]


def get_resp(resp) -> flask.wrappers.Response:
    if not isinstance(resp, flask.wrappers.Response):
        return make_response(resp)
    return resp


def add_cors_header(resp: flask.wrappers.Response, header: str, value: str):
    if header in resp.headers:
        resp.headers[header] += f", {value}"
    else:
        resp.headers[header] = value


def cors_decorator(header: str, value: str):
    def decorator(f):
        @wraps(f)
        def cors_wrapper(*args, **kwargs):
            resp = get_resp(f(*args, **kwargs))
            add_cors_header(resp, header, value)
            return resp

        return cors_wrapper

    return decorator


def allow_origin(origin="*"):
    return cors_decorator("Access-Control-Allow-Origin", origin)


def allow_credentials():
    return cors_decorator("Access-Control-Allow-Credentials", "true")


def allow_methods(methods="GET, POST, OPTIONS"):
    return cors_decorator("Access-Control-Allow-Methods", methods)


def allow_headers(headers="Content-Type, Authorization"):
    return cors_decorator("Access-Control-Allow-Headers", headers)
