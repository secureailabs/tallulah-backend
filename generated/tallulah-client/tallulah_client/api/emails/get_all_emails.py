from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_multiple_email_out import GetMultipleEmailOut
from ...models.validation_error import ValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    mailbox_id: str,
    skip: Union[Unset, None, int] = 0,
    limit: Union[Unset, None, int] = 20,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    params["mailbox_id"] = mailbox_id

    params["skip"] = skip

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": "/emails/",
        "params": params,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetMultipleEmailOut, ValidationError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetMultipleEmailOut.from_dict(response.json())

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
) -> Response[Union[GetMultipleEmailOut, ValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    mailbox_id: str,
    skip: Union[Unset, None, int] = 0,
    limit: Union[Unset, None, int] = 20,
) -> Response[Union[GetMultipleEmailOut, ValidationError]]:
    """Get All Emails

     Get all the emails from the mailbox

    Args:
        mailbox_id (str): Mailbox id
        skip (Union[Unset, None, int]): Number of emails to skip
        limit (Union[Unset, None, int]): Number of emails to return Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetMultipleEmailOut, ValidationError]]
    """

    kwargs = _get_kwargs(
        mailbox_id=mailbox_id,
        skip=skip,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    mailbox_id: str,
    skip: Union[Unset, None, int] = 0,
    limit: Union[Unset, None, int] = 20,
) -> Optional[Union[GetMultipleEmailOut, ValidationError]]:
    """Get All Emails

     Get all the emails from the mailbox

    Args:
        mailbox_id (str): Mailbox id
        skip (Union[Unset, None, int]): Number of emails to skip
        limit (Union[Unset, None, int]): Number of emails to return Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetMultipleEmailOut, ValidationError]
    """

    return sync_detailed(
        client=client,
        mailbox_id=mailbox_id,
        skip=skip,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    mailbox_id: str,
    skip: Union[Unset, None, int] = 0,
    limit: Union[Unset, None, int] = 20,
) -> Response[Union[GetMultipleEmailOut, ValidationError]]:
    """Get All Emails

     Get all the emails from the mailbox

    Args:
        mailbox_id (str): Mailbox id
        skip (Union[Unset, None, int]): Number of emails to skip
        limit (Union[Unset, None, int]): Number of emails to return Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetMultipleEmailOut, ValidationError]]
    """

    kwargs = _get_kwargs(
        mailbox_id=mailbox_id,
        skip=skip,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    mailbox_id: str,
    skip: Union[Unset, None, int] = 0,
    limit: Union[Unset, None, int] = 20,
) -> Optional[Union[GetMultipleEmailOut, ValidationError]]:
    """Get All Emails

     Get all the emails from the mailbox

    Args:
        mailbox_id (str): Mailbox id
        skip (Union[Unset, None, int]): Number of emails to skip
        limit (Union[Unset, None, int]): Number of emails to return Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetMultipleEmailOut, ValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            mailbox_id=mailbox_id,
            skip=skip,
            limit=limit,
        )
    ).parsed
