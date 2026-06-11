from datetime import datetime, timedelta

import jwt
from flask import request

import nxcore.config as base_config


def normalize_token(t: str) -> str:
    if not t:
        raise Exception("Missing token")

    token = t.strip()

    if token.startswith("Bearer "):
        token = token[7:]

    if token.count('.') != 2:
        raise Exception(f"JWT malformed: {repr(token)}")

    return token


def jwt_get_principal():
    """
    Get the principal from the JWT token.

    Returns:
        dict: The principal of the user.
    """
    token = jwt_get()
    return jwt_decode(token).get("profile", {})


def jwt_get():
    token = request.headers.get("Authorization", None)
    if token:
        return normalize_token(token)
    return None


def jwt_get_refresh():
    token = request.headers.get("Refresh-Token", None)
    if token:
        return normalize_token(token)
    return None


def jwt_decode(token):
    return jwt.decode(token,
                      base_config.get('JWT_SECRET_KEY'),
                      algorithms=["HS256"],
                      audience=base_config.get('JWT_AUD')
                      )


def jwt_create_access_token(sub, profile=None, authorities=None, extra_clains=None):
    now = datetime.now(base_config.get('TZ'))
    if profile:
        profile.pop("created_at", None)
        profile.pop("updated_at", None)
        profile.pop("password", None)
    payload = {
        "exp": int((now + timedelta(seconds=base_config.get('JWT_EXPIRE'))).timestamp()),
        "iat": int(now.timestamp()),
        "sub": sub,
        "profile": profile,
        "authorities": authorities,
        "aud": base_config.get('JWT_AUD'),
    }
    if extra_clains:
        payload.update(extra_clains)
    return jwt.encode(payload, base_config.get('JWT_SECRET_KEY'), algorithm="HS256")


def jwt_create_refresh_token(sub):
    now = datetime.now(base_config.get('TZ')) + timedelta(hours=24)
    payload = {"exp": int(now.timestamp()), "sub": str(sub), "aud": base_config.get('JWT_AUD')}
    return jwt.encode(payload, base_config.get('JWT_SECRET_KEY'), algorithm="HS256")
