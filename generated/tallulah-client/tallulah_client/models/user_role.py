from enum import Enum


class UserRole(str, Enum):
    SAIL_ADMIN = "SAIL_ADMIN"
    USER = "USER"

    def __str__(self) -> str:
        return str(self.value)
