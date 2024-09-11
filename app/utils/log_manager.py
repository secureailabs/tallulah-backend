import json
import logging
from enum import Enum
from time import time
from typing import Dict

logger = logging.getLogger("uvicorn.info")
logger.setLevel(logging.INFO)


class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


def _add_log_message(
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
    elif level == LogLevel.DEBUG:
        logger.debug(message_str)
    else:
        raise ValueError("Invalid log level")
    pass


def INFO(message: Dict):
    _add_log_message(LogLevel.INFO, message)


def WARNING(message: Dict):
    _add_log_message(LogLevel.WARNING, message)


def ERROR(message: Dict):
    _add_log_message(LogLevel.ERROR, message)


def DEBUG(message: Dict):
    _add_log_message(LogLevel.DEBUG, message)
