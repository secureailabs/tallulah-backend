from enum import Enum


class EmailState(str, Enum):
    FAILED = "FAILED"
    PROCESSED = "PROCESSED"
    UNPROCESSED = "UNPROCESSED"

    def __str__(self) -> str:
        return str(self.value)
