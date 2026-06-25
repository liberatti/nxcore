import os
import tempfile
import socket
from datetime import datetime
from bson import ObjectId

import nxcore.config as base_config
from nxcore.common_utils import (
    deep_merge,
    deep_date_str,
    hash_dict,
    json_serial,
    gen_random_string,
    replace_tz,
    get_server_id,
    clear_directory
)


def test_deep_merge():
    a = {"x": 1, "y": {"a": 1, "b": 2}}
    b = {"y": {"b": 3, "c": 4}, "z": 5}
    expected = {"x": 1, "y": {"a": 1, "b": 3, "c": 4}, "z": 5}
    assert deep_merge(a, b) == expected


def test_deep_date_str():
    now = datetime(2026, 6, 25, 12, 0, 0)
    data = {
        "date": now,
        "list": [now, {"nested": now}]
    }
    result = deep_date_str(data)
    expected = {
        "date": now.isoformat(),
        "list": [now.isoformat(), {"nested": now.isoformat()}]
    }
    assert result == expected


def test_hash_dict():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    assert hash_dict(d1) == hash_dict(d2)


def test_json_serial():
    now = datetime(2026, 6, 25, 12, 0, 0)
    assert json_serial(now) == now.isoformat()

    b = b"hello"
    import base64
    assert json_serial(b) == base64.b64encode(b).decode("utf-8")

    obj_id = ObjectId()
    assert json_serial(obj_id) == str(obj_id)

    try:
        json_serial(set())
        assert False, "Should raise TypeError"
    except TypeError:
        pass


def test_gen_random_string():
    s = gen_random_string(10)
    assert len(s) == 10
    assert s.islower()


def test_replace_tz():
    dt = datetime(2026, 6, 25, 12, 0, 0)
    result = replace_tz(dt)
    assert result.tzinfo == base_config.get("TZ")


def test_get_server_id():
    os.environ["SERVERID"] = "test-server"
    try:
        assert get_server_id() == "test-server"
    finally:
        del os.environ["SERVERID"]

    assert get_server_id() == socket.getfqdn()


def test_clear_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "file.txt")
        with open(file_path, "w") as f:
            f.write("test")

        subdir = os.path.join(tmpdir, "subdir")
        os.mkdir(subdir)
        subfile = os.path.join(subdir, "subfile.txt")
        with open(subfile, "w") as f:
            f.write("subtest")

        assert os.path.exists(file_path)
        assert os.path.exists(subdir)

        clear_directory(tmpdir)

        assert os.path.exists(tmpdir)
        assert len(os.listdir(tmpdir)) == 0
