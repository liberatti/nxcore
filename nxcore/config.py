import pytz

_config = {
    'DATETIME_FMT': "%Y-%m-%dT%H:%M:%S.%fZ",
    'TZ': pytz.timezone("UTC"),
    'SECURITY_ENABLED': True,
    'JWT_AUD': 'app',
    'JWT_SECRET_KEY': 'dev',
    'JWT_EXPIRE': 1800,
    'LOGLEVEL': 'INFO',
    'CORE_VERSION': 'v0.0.2'
}


def init(overrides: dict = None):
    """
    Initializes the configuration with optional overrides.

    Args:
        overrides (dict, optional): A dictionary of configuration keys and values to override.
    """
    if overrides:
        _config.update(overrides)


def get(key, default=None):
    """
    Retrieves a configuration value by its key.

    Args:
        key (str): The configuration key.
        default (object, optional): The default value to return if the key is not found.

    Returns:
        object: The configuration value or the default.
    """
    return _config.get(key, default)


def has(keys):
    """
    Checks if a configuration key exists.

    Args:
        keys (str): The configuration key to check.

    Returns:
        bool: True if the key exists, False otherwise.
    """
    return keys in _config
