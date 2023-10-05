import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define, field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetMailboxOut")


@define
class GetMailboxOut:
    """
    Attributes:
        email (str):
        user_id (str):
        id (str):
        creation_time (datetime.datetime):
        note (Union[Unset, str]):
    """

    email: str
    user_id: str
    id: str
    creation_time: datetime.datetime
    note: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        email = self.email
        user_id = self.user_id
        id = self.id
        creation_time = self.creation_time.isoformat()

        note = self.note

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "user_id": user_id,
                "id": id,
                "creation_time": creation_time,
            }
        )
        if note is not UNSET:
            field_dict["note"] = note

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        user_id = d.pop("user_id")

        id = d.pop("id")

        creation_time = isoparse(d.pop("creation_time"))

        note = d.pop("note", UNSET)

        get_mailbox_out = cls(
            email=email,
            user_id=user_id,
            id=id,
            creation_time=creation_time,
            note=note,
        )

        get_mailbox_out.additional_properties = d
        return get_mailbox_out

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
