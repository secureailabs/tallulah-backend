from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_mailbox_out import GetMailboxOut
from ...models.validation_error import ValidationError
from ...types import Response


def _get_kwargs(
    mailbox_id: str,
) -> Dict[str, Any]:
    pass

    return {
        "method": "get",
        "url": "/mailbox/{mailbox_id}".format(
            mailbox_id=mailbox_id,
        ),
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetMailboxOut, ValidationError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetMailboxOut.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = ValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[GetMailboxOut, ValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    mailbox_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[GetMailboxOut, ValidationError]]:
    """Get Mailbox

     Get the mailbox for the current user

    Args:
        mailbox_id (str): Mailbox id

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetMailboxOut, ValidationError]]
    """

    kwargs = _get_kwargs(
        mailbox_id=mailbox_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    mailbox_id: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[GetMailboxOut, ValidationError]]:
    """Get Mailbox

     Get the mailbox for the current user

    Args:
        mailbox_id (str): Mailbox id

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetMailboxOut, ValidationError]
    """

    return sync_detailed(
        mailbox_id=mailbox_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    mailbox_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[GetMailboxOut, ValidationError]]:
    """Get Mailbox

     Get the mailbox for the current user

    Args:
        mailbox_id (str): Mailbox id

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetMailboxOut, ValidationError]]
    """

    kwargs = _get_kwargs(
        mailbox_id=mailbox_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    mailbox_id: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[GetMailboxOut, ValidationError]]:
    """Get Mailbox

     Get the mailbox for the current user

    Args:
        mailbox_id (str): Mailbox id

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetMailboxOut, ValidationError]
    """

    return (
        await asyncio_detailed(
            mailbox_id=mailbox_id,
            client=client,
        )
    ).parsed
