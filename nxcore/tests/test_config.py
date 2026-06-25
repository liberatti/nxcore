import pytz
import nxcore.config as base_config


def test_config_get():
    assert base_config.get("JWT_AUD") == "app"
    assert base_config.get("NON_EXISTING", "default_val") == "default_val"


def test_config_has():
    assert base_config.has("SECURITY_ENABLED") is True
    assert base_config.has("NON_EXISTING") is False


def test_config_init():
    orig_fmt = base_config.get("DATETIME_FMT")
    orig_tz = base_config.get("TZ")

    try:
        new_tz = pytz.timezone("America/Sao_Paulo")
        base_config.init({
            "DATETIME_FMT": "%d/%m/%Y %H:%M:%S",
            "TZ": new_tz,
            "NEW_KEY": "new_val"
        })

        assert base_config.get("DATETIME_FMT") == "%d/%m/%Y %H:%M:%S"
        assert base_config.get("TZ") == new_tz
        assert base_config.get("NEW_KEY") == "new_val"
    finally:
        base_config.init({
            "DATETIME_FMT": orig_fmt,
            "TZ": orig_tz
        })
