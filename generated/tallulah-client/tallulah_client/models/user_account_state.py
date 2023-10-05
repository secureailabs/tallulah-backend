from enum import Enum


class UserAccountState(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"

    def __str__(self) -> str:
        return str(self.value)
