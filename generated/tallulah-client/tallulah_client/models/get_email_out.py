import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define, field
from dateutil.parser import isoparse

from ..models.email_state import EmailState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_email_out_body import GetEmailOutBody
    from ..models.get_email_out_from_address import GetEmailOutFromAddress


T = TypeVar("T", bound="GetEmailOut")


@define
class GetEmailOut:
    """
    Attributes:
        subject (str):
        body (GetEmailOutBody):
        from_address (GetEmailOutFromAddress):
        received_time (datetime.datetime):
        mailbox_id (str):
        id (str):
        creation_time (datetime.datetime):
        note (Union[Unset, str]):
        tags (Union[Unset, List[str]]):
        message_state (Union[Unset, EmailState]): An enumeration. Default: EmailState.UNPROCESSED.
    """

    subject: str
    body: "GetEmailOutBody"
    from_address: "GetEmailOutFromAddress"
    received_time: datetime.datetime
    mailbox_id: str
    id: str
    creation_time: datetime.datetime
    note: Union[Unset, str] = UNSET
    tags: Union[Unset, List[str]] = UNSET
    message_state: Union[Unset, EmailState] = EmailState.UNPROCESSED
    additional_properties: Dict[str, Any] = field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        subject = self.subject
        body = self.body.to_dict()

        from_address = self.from_address.to_dict()

        received_time = self.received_time.isoformat()

        mailbox_id = self.mailbox_id
        id = self.id
        creation_time = self.creation_time.isoformat()

        note = self.note
        tags: Union[Unset, List[str]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        message_state: Union[Unset, str] = UNSET
        if not isinstance(self.message_state, Unset):
            message_state = self.message_state.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "subject": subject,
                "body": body,
                "from_address": from_address,
                "received_time": received_time,
                "mailbox_id": mailbox_id,
                "id": id,
                "creation_time": creation_time,
            }
        )
        if note is not UNSET:
            field_dict["note"] = note
        if tags is not UNSET:
            field_dict["tags"] = tags
        if message_state is not UNSET:
            field_dict["message_state"] = message_state

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_email_out_body import GetEmailOutBody
        from ..models.get_email_out_from_address import GetEmailOutFromAddress

        d = src_dict.copy()
        subject = d.pop("subject")

        body = GetEmailOutBody.from_dict(d.pop("body"))

        from_address = GetEmailOutFromAddress.from_dict(d.pop("from_address"))

        received_time = isoparse(d.pop("received_time"))

        mailbox_id = d.pop("mailbox_id")

        id = d.pop("id")

        creation_time = isoparse(d.pop("creation_time"))

        note = d.pop("note", UNSET)

        tags = cast(List[str], d.pop("tags", UNSET))

        _message_state = d.pop("message_state", UNSET)
        message_state: Union[Unset, EmailState]
        if isinstance(_message_state, Unset):
            message_state = UNSET
        else:
            message_state = EmailState(_message_state)

        get_email_out = cls(
            subject=subject,
            body=body,
            from_address=from_address,
            received_time=received_time,
            mailbox_id=mailbox_id,
            id=id,
            creation_time=creation_time,
            note=note,
            tags=tags,
            message_state=message_state,
        )

        get_email_out.additional_properties = d
        return get_email_out

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
