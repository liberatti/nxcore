import logging

import nxcore.config as base_config


class CustomLogger(logging.Logger):
    def info(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        super().info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        super().error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        super().warning(msg, *args, **kwargs)


formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s-"
    "[%(filename)s][%(funcName)s][%(lineno)d] %(message)s"
)
logging.setLoggerClass(CustomLogger)

logger = logging.getLogger(__name__)

level = getattr(logging, base_config.get("LOGLEVEL"), logging.INFO)
logger.setLevel(level)

console_handler = logging.StreamHandler()
console_handler.setLevel(level)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# evita duplicação
logger.propagate = False

# silencia libs externas
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
