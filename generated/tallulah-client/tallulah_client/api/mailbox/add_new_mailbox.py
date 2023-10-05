from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_exception_obj import HTTPExceptionObj
from ...models.register_mailbox_in import RegisterMailboxIn
from ...models.register_mailbox_out import RegisterMailboxOut
from ...models.validation_error import ValidationError
from ...types import Response


def _get_kwargs(
    *,
    json_body: RegisterMailboxIn,
) -> Dict[str, Any]:
    pass

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": "/mailbox/",
        "json": json_json_body,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]]:
    if response.status_code == HTTPStatus.ACCEPTED:
        response_202 = RegisterMailboxOut.from_dict(response.json())

        return response_202
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = ValidationError.from_dict(response.json())

        return response_422
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = HTTPExceptionObj.from_dict(response.json())

        return response_400
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: RegisterMailboxIn,
) -> Response[Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]]:
    """Add New Mailbox

     Add a new mailbox by code

    Args:
        json_body (RegisterMailboxIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]]
    """

    kwargs = _get_kwargs(
        json_body=json_body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    json_body: RegisterMailboxIn,
) -> Optional[Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]]:
    """Add New Mailbox

     Add a new mailbox by code

    Args:
        json_body (RegisterMailboxIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: RegisterMailboxIn,
) -> Response[Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]]:
    """Add New Mailbox

     Add a new mailbox by code

    Args:
        json_body (RegisterMailboxIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]]
    """

    kwargs = _get_kwargs(
        json_body=json_body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    json_body: RegisterMailboxIn,
) -> Optional[Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]]:
    """Add New Mailbox

     Add a new mailbox by code

    Args:
        json_body (RegisterMailboxIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPExceptionObj, RegisterMailboxOut, ValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
        )
    ).parsed
