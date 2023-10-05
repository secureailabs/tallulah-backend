from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define, field

if TYPE_CHECKING:
    from ..models.get_mailbox_out import GetMailboxOut


T = TypeVar("T", bound="GetMultipleMailboxesOut")


@define
class GetMultipleMailboxesOut:
    """
    Attributes:
        mailboxes (List['GetMailboxOut']):
    """

    mailboxes: List["GetMailboxOut"]
    additional_properties: Dict[str, Any] = field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        mailboxes = []
        for mailboxes_item_data in self.mailboxes:
            mailboxes_item = mailboxes_item_data.to_dict()

            mailboxes.append(mailboxes_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "mailboxes": mailboxes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_mailbox_out import GetMailboxOut

        d = src_dict.copy()
        mailboxes = []
        _mailboxes = d.pop("mailboxes")
        for mailboxes_item_data in _mailboxes:
            mailboxes_item = GetMailboxOut.from_dict(mailboxes_item_data)

            mailboxes.append(mailboxes_item)

        get_multiple_mailboxes_out = cls(
            mailboxes=mailboxes,
        )

        get_multiple_mailboxes_out.additional_properties = d
        return get_multiple_mailboxes_out

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
