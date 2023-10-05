from typing import Any, Dict, List, Type, TypeVar

from attrs import define, field

from ..models.mailbox_provider import MailboxProvider

T = TypeVar("T", bound="RegisterMailboxIn")


@define
class RegisterMailboxIn:
    """
    Attributes:
        code (str):
        provider (MailboxProvider): An enumeration.
    """

    code: str
    provider: MailboxProvider
    additional_properties: Dict[str, Any] = field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        code = self.code
        provider = self.provider.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "provider": provider,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        code = d.pop("code")

        provider = MailboxProvider(d.pop("provider"))

        register_mailbox_in = cls(
            code=code,
            provider=provider,
        )

        register_mailbox_in.additional_properties = d
        return register_mailbox_in

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
