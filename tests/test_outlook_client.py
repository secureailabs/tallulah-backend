import os

import pytest

from app.utils.emails import EmailAddress, EmailBody, Message, MessageResponse, OutlookClient, ToRecipient


@pytest.fixture
def client_id():
    return os.environ.get("OUTLOOK_CLIENT_ID")


@pytest.fixture
def client_secret():
    return os.environ.get("OUTLOOK_CLIENT_SECRET")


@pytest.fixture
def redirect_uri():
    return os.environ.get("OUTLOOK_REDIRECT_URI")


@pytest.fixture
def refresh_token():
    return os.environ.get("OUTLOOK_REFRESH_TOKEN")


@pytest.fixture
def client(client_id, client_secret, redirect_uri):
    return OutlookClient(client_id, client_secret, redirect_uri)


def test_env_vars(client_id, client_secret, redirect_uri, refresh_token):
    assert client_id
    assert client_secret
    assert redirect_uri
    assert refresh_token


@pytest.mark.asyncio
async def test_connect_with_refresh_token(client: OutlookClient, refresh_token):
    await client.connect_with_refresh_token(refresh_token)
    assert client.token
    assert client.refresh_token
    return client


@pytest.mark.asyncio
async def test_reauthenticate(client: OutlookClient, refresh_token):
    await client.connect_with_refresh_token(refresh_token)
    await client.reauthenticate()


@pytest.mark.asyncio
async def test_get_user_info(client: OutlookClient, refresh_token: str):
    await client.connect_with_refresh_token(refresh_token)
    result = await client.get_user_info()
    assert "displayName" in result
    assert "mail" in result


@pytest.mark.asyncio
async def test_receive_email(client: OutlookClient, refresh_token: str):
    await client.connect_with_refresh_token(refresh_token)
    result = await client.receive_email()

    assert type(result) == list
    assert len(result) > 0
    assert "subject" in result[0]
    assert "bodyPreview" in result[0]
    assert "sender" in result[0]
    assert "emailAddress" in result[0]["sender"]
    assert "name" in result[0]["sender"]["emailAddress"]
    assert "address" in result[0]["sender"]["emailAddress"]
    assert "toRecipients" in result[0]
    assert "emailAddress" in result[0]["toRecipients"][0]
    assert "name" in result[0]["toRecipients"][0]["emailAddress"]
    assert "address" in result[0]["toRecipients"][0]["emailAddress"]
    assert "receivedDateTime" in result[0]


@pytest.mark.asyncio
async def test_receive_email_later(client: OutlookClient, refresh_token: str):
    await client.connect_with_refresh_token(refresh_token)
    result = await client.receive_email()
    assert type(result) == list
    assert len(result) > 1

    result = await client.receive_email(received_after=result[1]["receivedDateTime"])
    assert type(result) == list
    assert len(result) > 0


def test_message_response_object():
    response = MessageResponse(
        message=Message(
            body=EmailBody(content="test", contentType="Text"),
            toRecipients=[ToRecipient(emailAddress=EmailAddress(address="test@arin.com", name="test"))],
        )
    )


def test_message_response_comment_body_both_present_validation():
    with pytest.raises(ValueError):
        MessageResponse(
            message=Message(
                body=EmailBody(content="test", contentType="Text"),
                toRecipients=[ToRecipient(emailAddress=EmailAddress(address="test@arin.com", name="test"))],
            ),
            comment="test",
        )


def test_message_response_comment_body_none_present_validation():
    with pytest.raises(ValueError):
        MessageResponse(
            message=Message(
                toRecipients=[ToRecipient(emailAddress=EmailAddress(address="test@arin.com", name="test"))],
            ),
        )


@pytest.mark.asyncio
async def test_reply_email(client: OutlookClient, refresh_token: str):
    await client.connect_with_refresh_token(refresh_token)
    result = await client.receive_email()
    assert type(result) == list
    assert len(result) > 0

    await client.reply_email(
        email_id=result[0]["id"],
        message=MessageResponse(
            message=Message(body=EmailBody(content="this is a test response. Kindly ignore", contentType="text")),
        ),
    )


@pytest.mark.asyncio
async def test_reply_email_with_subject(client: OutlookClient, refresh_token: str):
    await client.connect_with_refresh_token(refresh_token)
    result = await client.receive_email()
    assert type(result) == list
    assert len(result) > 0

    await client.reply_email(
        email_id=result[0]["id"],
        message=MessageResponse(
            message=Message(
                subject="Test reply subject",
                body=EmailBody(content="this is a test response. Kindly ignore", contentType="text"),
            ),
        ),
    )
