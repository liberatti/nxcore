import pytz

_config = {
    "DATETIME_FMT": "%Y-%m-%dT%H:%M:%S.%fZ",
    "TZ": pytz.timezone("UTC"),
    "SECURITY_ENABLED": True,
    "JWT_AUD": "app",
    "JWT_SECRET_KEY": "dev",
    "JWT_EXPIRE": 1800,
    "LOGLEVEL": "INFO",
}


def init(overrides: dict[str, any] | None = None) -> None:
    """Initializes the configuration with optional overrides.

    Args:
        overrides (dict, optional): A dictionary of configuration keys and values to override.
    """
    if overrides:
        _config.update(overrides)


def get(key: str, default: any = None) -> any:
    """Retrieves a configuration value by its key.

    Args:
        key (str): The configuration key.
        default (any, optional): The default value to return if the key is not found.

    Returns:
        any: The configuration value or the default.
    """
    return _config.get(key, default)


def has(keys: str) -> bool:
    """Checks if a configuration key exists.

    Args:
        keys (str): The configuration key to check.

    Returns:
        bool: True if the key exists, False otherwise.
    """
    return keys in _config
