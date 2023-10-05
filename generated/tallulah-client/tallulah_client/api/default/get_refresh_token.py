from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_exception_obj import HTTPExceptionObj
from ...models.login_success_out import LoginSuccessOut
from ...models.refresh_token_in import RefreshTokenIn
from ...models.validation_error import ValidationError
from ...types import Response


def _get_kwargs(
    *,
    json_body: RefreshTokenIn,
) -> Dict[str, Any]:
    pass

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": "/refresh-token",
        "json": json_json_body,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = LoginSuccessOut.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = ValidationError.from_dict(response.json())

        return response_422
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        response_401 = HTTPExceptionObj.from_dict(response.json())

        return response_401
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: RefreshTokenIn,
) -> Response[Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]]:
    """Refresh For Access Token

     Refresh the JWT token for the user

    Args:
        json_body (RefreshTokenIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]]
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
    client: Union[AuthenticatedClient, Client],
    json_body: RefreshTokenIn,
) -> Optional[Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]]:
    """Refresh For Access Token

     Refresh the JWT token for the user

    Args:
        json_body (RefreshTokenIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: RefreshTokenIn,
) -> Response[Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]]:
    """Refresh For Access Token

     Refresh the JWT token for the user

    Args:
        json_body (RefreshTokenIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]]
    """

    kwargs = _get_kwargs(
        json_body=json_body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: RefreshTokenIn,
) -> Optional[Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]]:
    """Refresh For Access Token

     Refresh the JWT token for the user

    Args:
        json_body (RefreshTokenIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPExceptionObj, LoginSuccessOut, ValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
        )
    ).parsed
