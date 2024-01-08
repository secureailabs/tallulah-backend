import json
import logging
from enum import Enum
from time import time
from typing import Dict

logger = logging.getLogger("apiservice")
handler = logging.FileHandler("audit.log")
logger.setLevel(logging.INFO)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


def add_log_message(
    level: LogLevel,
    message: Dict,
):
    message["timestamp"] = time()
    message["level"] = level.value
    message_str = json.dumps(message)

    if level == LogLevel.INFO:
        logger.info(message_str)
    elif level == LogLevel.WARNING:
        logger.warning(message_str)
    elif level == LogLevel.ERROR:
        logger.error(message_str)
    else:
        raise ValueError("Invalid log level")
    pass