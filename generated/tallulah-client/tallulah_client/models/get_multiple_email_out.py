from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define, field

if TYPE_CHECKING:
    from ..models.get_email_out import GetEmailOut


T = TypeVar("T", bound="GetMultipleEmailOut")


@define
class GetMultipleEmailOut:
    """
    Attributes:
        messages (List['GetEmailOut']):
        next_ (int):
        limit (int):
    """

    messages: List["GetEmailOut"]
    next_: int
    limit: int
    additional_properties: Dict[str, Any] = field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()

            messages.append(messages_item)

        next_ = self.next_
        limit = self.limit

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "messages": messages,
                "next": next_,
                "limit": limit,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_email_out import GetEmailOut

        d = src_dict.copy()
        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = GetEmailOut.from_dict(messages_item_data)

            messages.append(messages_item)

        next_ = d.pop("next")

        limit = d.pop("limit")

        get_multiple_email_out = cls(
            messages=messages,
            next_=next_,
            limit=limit,
        )

        get_multiple_email_out.additional_properties = d
        return get_multiple_email_out

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
