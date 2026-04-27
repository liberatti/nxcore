import base64
import hashlib
import json
import os
import random
import shutil
import socket
import string
import zipfile
from copy import deepcopy
from datetime import datetime

from bson import ObjectId

import nxcore.config as base_config
from nxcore.middleware.logging import logger


def clear_directory(directory_path):
    """
    Deletes all files and subdirectories within the specified directory.

    Args:
        directory_path (str): The path to the directory to clear.
    """
    if os.path.exists(directory_path):
        try:
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        except Exception as e:
            logger.error(e)


def unpack_zip(content, target_dir="/var/www"):
    """
    Unpacks a ZIP file from bytes into the target directory.

    Args:
        content (bytes): The binary content of the ZIP file.
        target_dir (str, optional): The directory to extract into. Defaults to "/var/www".
    """
    os.mkdir(target_dir)
    zip_file_path = os.path.join(target_dir, "unpack.zip")
    with open(zip_file_path, "wb") as zip_file:
        zip_file.write(content)
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(target_dir)
    os.remove(zip_file_path)


def get_server_id():
    """
    Retrieves the server identifier from environment variables or hostname.

    Returns:
        str: The server ID.
    """
    server_ = os.getenv("SERVERID")
    if server_ is None:
        server_ = socket.getfqdn()
    return server_


def deep_date_str(obj):
    """
    Recursively converts all datetime objects in a dictionary or list to ISO format strings.

    Args:
        obj (dict or list): The object to process.

    Returns:
        dict or list: A deep copy of the object with formatted dates.
    """
    _obj = deepcopy(obj)
    for key, value in _obj.items():
        if isinstance(value, datetime):
            _obj[key] = value.isoformat()
        elif isinstance(value, dict):
            deep_date_str(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    deep_date_str(item)
    return _obj


def deep_merge(a: dict, b: dict) -> dict:
    """
    Recursively merges two dictionaries.

    Args:
        a (dict): The base dictionary.
        b (dict): The dictionary with values to merge into 'a'.

    Returns:
        dict: The merged dictionary.
    """
    result = deepcopy(a)
    for bk, bv in b.items():
        av = result.get(bk)
        if isinstance(av, dict) and isinstance(bv, dict):
            result[bk] = deep_merge(av, bv)
        else:
            result[bk] = deepcopy(bv)
    return result


def hash_dict(d):
    """
    Generates an MD5 hash of a dictionary.

    Args:
        d (dict): The dictionary to hash.

    Returns:
        str: The MD5 hex digest.
    """
    json_str = json.dumps(d, sort_keys=True, default=json_serial)
    return hashlib.md5(json_str.encode()).hexdigest()


def json_serial(obj):
    """
    JSON serializer for objects not supported by default json package.
    Supports datetime, bytes, and ObjectId.

    Args:
        obj (object): The object to serialize.

    Returns:
        str: The serialized value.

    Raises:
        TypeError: If the type is not serializable.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"non-serializable type: {type(obj)}")


def gen_random_string(length=16):
    """
    Generates a random string of lowercase letters.

    Args:
        length (int, optional): Length of the string. Defaults to 16.

    Returns:
        str: The random string.
    """
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def replace_tz(not_valid_before):
    """
    Ensures a datetime object has the correct timezone and converts it to the configured timezone.

    Args:
        not_valid_before (datetime): The datetime object to process.

    Returns:
        datetime: The processed datetime object with correct timezone.
    """
    if not_valid_before.tzinfo is None:
        crt_not_valid_before = not_valid_before.replace(tzinfo=base_config.get("TZ"))
    else:
        crt_not_valid_before = not_valid_before
    return crt_not_valid_before.astimezone(base_config.get("TZ"))
