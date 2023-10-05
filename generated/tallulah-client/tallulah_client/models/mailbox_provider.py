from enum import Enum


class MailboxProvider(str, Enum):
    GMAIL = "GMAIL"
    OUTLOOK = "OUTLOOK"

    def __str__(self) -> str:
        return str(self.value)
