from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define, field

from ..models.user_account_state import UserAccountState
from ..models.user_role import UserRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateUserIn")


@define
class UpdateUserIn:
    """
    Attributes:
        job_title (Union[Unset, str]):
        roles (Union[Unset, List[UserRole]]):
        account_state (Union[Unset, UserAccountState]): An enumeration.
        avatar (Union[Unset, str]):
    """

    job_title: Union[Unset, str] = UNSET
    roles: Union[Unset, List[UserRole]] = UNSET
    account_state: Union[Unset, UserAccountState] = UNSET
    avatar: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        job_title = self.job_title
        roles: Union[Unset, List[str]] = UNSET
        if not isinstance(self.roles, Unset):
            roles = []
            for roles_item_data in self.roles:
                roles_item = roles_item_data.value

                roles.append(roles_item)

        account_state: Union[Unset, str] = UNSET
        if not isinstance(self.account_state, Unset):
            account_state = self.account_state.value

        avatar = self.avatar

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if job_title is not UNSET:
            field_dict["job_title"] = job_title
        if roles is not UNSET:
            field_dict["roles"] = roles
        if account_state is not UNSET:
            field_dict["account_state"] = account_state
        if avatar is not UNSET:
            field_dict["avatar"] = avatar

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        job_title = d.pop("job_title", UNSET)

        roles = []
        _roles = d.pop("roles", UNSET)
        for roles_item_data in _roles or []:
            roles_item = UserRole(roles_item_data)

            roles.append(roles_item)

        _account_state = d.pop("account_state", UNSET)
        account_state: Union[Unset, UserAccountState]
        if isinstance(_account_state, Unset):
            account_state = UNSET
        else:
            account_state = UserAccountState(_account_state)

        avatar = d.pop("avatar", UNSET)

        update_user_in = cls(
            job_title=job_title,
            roles=roles,
            account_state=account_state,
            avatar=avatar,
        )

        update_user_in.additional_properties = d
        return update_user_in

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
