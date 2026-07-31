import logging
from typing import Any, Optional

try:
    from flask import Flask, current_app, has_app_context
except Exception:
    Flask = None
    current_app = None

    def has_app_context():
        return False


# Base package logger with NullHandler to prevent warnings
logger = logging.getLogger("nxcore")
logger.addHandler(logging.NullHandler())


class CustomLogger(logging.Logger):
    """Custom logger class that defaults the stacklevel to 2 to report the caller location."""

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an info message, defaulting stacklevel to 2."""
        kwargs.setdefault("stacklevel", 2)
        super().info(msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an error message, defaulting stacklevel to 2."""
        kwargs.setdefault("stacklevel", 2)
        super().error(msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a warning message, defaulting stacklevel to 2."""
        kwargs.setdefault("stacklevel", 2)
        super().warning(msg, *args, **kwargs)


class LoggingManager:
    """Flask extension to configure logging format and levels for the application."""

    def __init__(self, app: Optional[Flask] = None, loglevel: Optional[str] = None):
        self.console_handler = None
        if app is not None:
            self.init_app(app)
        elif loglevel is not None:
            self.configure(loglevel)

    def configure(self, loglevel_name: str = "INFO") -> None:
        """Configures logging for the nxcore library and sets the custom logger class.

        Args:
            loglevel_name (str): Log level name (e.g. "INFO", "DEBUG").
        """
        logging.setLoggerClass(CustomLogger)

        level = getattr(logging, loglevel_name.upper(), logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s-"
            "[%(module)s.%(funcName)s (%(lineno)d)] %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.console_handler = console_handler

        lib_logger = logging.getLogger("nxcore")
        lib_logger.setLevel(level)

        # Clear existing handlers
        for h in list(lib_logger.handlers):
            lib_logger.removeHandler(h)

        gunicorn_logger = logging.getLogger("gunicorn.error")
        if gunicorn_logger.handlers:
            for h in gunicorn_logger.handlers:
                lib_logger.addHandler(h)
        else:
            lib_logger.addHandler(console_handler)

        lib_logger.propagate = False

        # Silence noisy external libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

    def init_app(self, app: Flask) -> None:
        """Initializes the extension with the Flask application.

        Args:
            app (Flask): The Flask application instance.
        """
        loglevel_name = app.config.get("LOGLEVEL", "INFO")
        self.configure(loglevel_name)

        level = getattr(logging, loglevel_name.upper(), logging.INFO)
        app.logger.setLevel(level)

        gunicorn_logger = logging.getLogger("gunicorn.error")
        if gunicorn_logger.handlers:
            for h in gunicorn_logger.handlers:
                app.logger.addHandler(h)
        elif self.console_handler:
            app.logger.addHandler(self.console_handler)

        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["logging_manager"] = self

    @classmethod
    def get_current_instance(cls) -> "LoggingManager":
        """Retrieves the LoggingManager instance from the active Flask application context.

        Returns:
            LoggingManager: The active LoggingManager instance.

        Raises:
            RuntimeError: If called outside application context or extension is not initialized.
        """
        if not has_app_context():
            raise RuntimeError(
                "Working outside of application context. "
                "Make sure a Flask application is active or use app.app_context()."
            )
        if (
            not hasattr(current_app, "extensions")
            or "logging_manager" not in current_app.extensions
        ):
            raise RuntimeError(
                "LoggingManager has not been initialized on this Flask application."
            )
        return current_app.extensions["logging_manager"]
