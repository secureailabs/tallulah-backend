import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _add_log_message(
    level: LogLevel,
    message: Dict,
):
    message["timestamp"] = datetime.now(timezone.utc).isoformat()
    message_str = json.dumps(message)

    if level == LogLevel.DEBUG:
        logger.debug(message_str)
    elif level == LogLevel.INFO:
        logger.info(message_str)
    elif level == LogLevel.WARNING:
        logger.warning(message_str)
    elif level == LogLevel.ERROR:
        logger.error(message_str)
    elif level == LogLevel.CRITICAL:
        logger.critical(message_str)
    else:
        raise ValueError("Invalid log level")
    pass


def DEBUG(message: Dict):
    _add_log_message(LogLevel.DEBUG, message)


def INFO(message: Dict):
    _add_log_message(LogLevel.INFO, message)


def WARNING(message: Dict):
    _add_log_message(LogLevel.WARNING, message)


def ERROR(message: Dict):
    _add_log_message(LogLevel.ERROR, message)


def CRITICAL(message: Dict):
    _add_log_message(LogLevel.CRITICAL, message)
