import traceback
from functools import wraps

import jwt
from flask import jsonify, request, Response

import nxcore.config as base_config
from nxcore.middleware.jwt import jwt_get, jwt_decode


def get_pagination():
    """
    Extracts pagination parameters (size and page) from the request arguments.

    Returns:
        dict or None: A dictionary containing 'per_page' and 'page' if both are present,
                      otherwise None.
    """
    _pagination = None
    if "size" in request.args and "page" in request.args:
        _pagination = {
            "per_page": int(request.args.get("size")),
            "page": int(request.args.get("page")),
        }
    return _pagination


def has_any_authority(authorities=None, _internal=False):
    """
    Decorator to check if the user has any of the required authorities.

    Args:
        authorities (list, optional): List of required authority strings. Defaults to None.
        _internal (bool, optional): Whether to allow internal API key access. Defaults to False.

    Returns:
        function: The decorated function or an error response (401/403).
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if not base_config.has("SECURITY_ENABLED") or not base_config.get(
                    "SECURITY_ENABLED"
            ):
                return fn(*args, **kwargs)

            if _internal and base_config.has("API_KEY") and base_config.get("API_KEY"):
                if base_config.get("API_KEY") == request.headers.get("x-api-key"):
                    return fn(*args, **kwargs)
            try:
                token = jwt_get()
                if token:
                    payload = jwt_decode(token)
                    if any(a in payload.get("authorities", []) for a in authorities):
                        return fn(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return response_error_401(
                    msg="Expired authorization", details=traceback.format_exc()
                )
            except Exception as e2:
                return response_error_401(msg=str(e2), details=traceback.format_exc())
            return response_error_403(message="Invalid authorization")

        return decorator

    return wrapper


def response_error_404():
    """
    Returns a standard 404 Not Found JSON response.

    Returns:
        tuple: (JSON response, status code 200)
    """
    return (
        jsonify(
            {
                "message": "No results found. Check url again",
                "code": 404,
                "url": request.url,
                "method": request.method,
            }
        ),
        200,
    )


def response_error(msg="Bad Request", details="", code=400):
    """
    Returns a generic error JSON response.

    Args:
        msg (str): Error message. Defaults to "Bad Request".
        details (str): Detailed error description. Defaults to "".
        code (int): HTTP status code. Defaults to 400.

    Returns:
        tuple: (JSON response, status code)
    """
    return (
        jsonify(
            {
                "message": msg,
                "code": code,
                "details": details,
                "url": request.url,
                "method": request.method,
            }
        ),
        code,
    )


def response_error_401(msg="Not authenticated", details=""):
    """
    Returns a standard 401 Unauthorized JSON response.

    Args:
        msg (str): Error message. Defaults to "Not authenticated".
        details (str): Detailed error description. Defaults to "".

    Returns:
        tuple: (JSON response, status code 401)
    """
    return (
        jsonify(
            {
                "message": msg,
                "code": 401,
                "details": details,
                "url": request.url,
                "method": request.method,
            }
        ),
        401,
    )


def response_error_403(message="Not authorized"):
    """
    Returns a standard 403 Forbidden JSON response.

    Args:
        message (str): Error message. Defaults to "Not authorized".

    Returns:
        tuple: (JSON response, status code 403)
    """
    return (
        jsonify(
            {
                "message": message,
                "code": 403,
                "url": request.url,
                "method": request.method,
            }
        ),
        403,
    )


def response_error_500(msg, code=500, details=""):
    """
    Returns a standard 500 Internal Server Error JSON response.

    Args:
        msg (str): Error message.
        code (int): HTTP status code. Defaults to 500.
        details (str): Detailed error description. Defaults to "".

    Returns:
        tuple: (JSON response, status code 500)
    """
    return (
        jsonify(
            {
                "message": msg,
                "details": details,
                "code": code,
                "url": request.url,
                "method": request.method,
            }
        ),
        500,
    )


def response_data_removed(desc):
    """
    Returns a JSON response indicating a record was removed.

    Args:
        desc (str): Description or ID of the removed record.

    Returns:
        tuple: (JSON response, status code 200)
    """
    return (
        jsonify({"message": f"Record {desc} removed", "code": 200}),
        200,
    )


def response_ok(desc):
    """
    Returns a generic successful JSON response.

    Args:
        desc (str): Message to include in the response.

    Returns:
        tuple: (JSON response, status code 200)
    """
    return (
        jsonify({"message": desc, "code": 200}),
        200,
    )


def response_error_parse(err):
    """
    Returns a 400 Bad Request JSON response for validation errors.

    Args:
        err (marshmallow.exceptions.ValidationError): The validation error object.

    Returns:
        tuple: (JSON response, status code 400)
    """
    return (
        jsonify(
            {
                "message": "Validation Error",
                "details": err.messages,
                "code": 400,
                "url": request.url,
                "method": request.method,
                # "valid_data": err.valid_data,
            }
        ),
        400,
    )


def response_data_list(o, schema=None, headers=None, status_code=200):
    """
    Returns a JSON response containing a list of data.

    Args:
        o (list): The list of data to return.
        schema (marshmallow.Schema, optional): Schema for serialization. Defaults to None.
        headers (dict, optional): Custom headers. Defaults to None.
        status_code (int, optional): HTTP status code. Defaults to 200.

    Returns:
        tuple: (JSON response, status code, headers)
    """
    if schema:
        return jsonify(schema.dump(o)), status_code, (headers or {})
    else:
        return jsonify(o), status_code, (headers or {})


def response_data(o, schema=None, headers=None, status_code=200):
    """
    Returns a JSON response containing a single data object.

    Args:
        o (object): The data object to return.
        schema (marshmallow.Schema, optional): Schema for serialization. Defaults to None.
        headers (dict, optional): Custom headers. Defaults to None.
        status_code (int, optional): HTTP status code. Defaults to 200.

    Returns:
        tuple: (JSON response, status code, headers)
    """
    if schema:
        return jsonify(schema.dump(o)), status_code, (headers or {})
    else:
        return jsonify(o), status_code, (headers or {})


def response_redirect(url, status_code=302):
    """
    Redirect to a specific URL
    :param url: The URL to redirect to
    :param status_code: HTTP status code (default: 302 - Found)
    :return: Response object with redirect
    """
    return Response(response=None, status=status_code, headers={"Location": url})
