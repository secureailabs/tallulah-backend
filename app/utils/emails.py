from typing import List, Optional, Union

import aiohttp
from azure.communication.email import EmailClient
from pydantic import BaseModel, validator
from tenacity import retry, stop_after_attempt, wait_fixed

from app.utils.secrets import secret_store


class EmailBody(BaseModel):
    contentType: str
    content: str


class EmailAddress(BaseModel):
    address: str
    name: str


class ToRecipient(BaseModel):
    emailAddress: EmailAddress


class Message(BaseModel):
    subject: Optional[str] = None
    body: Optional[EmailBody] = None
    toRecipients: Optional[List[ToRecipient]] = None


class MessageResponse(BaseModel):
    comment: Optional[str] = None
    message: Message

    # Only specifiy either 'Comment' or 'Body' property of the message object
    @validator("message")
    def comment_must_not_be_specified(cls, v: Message, values, **kwargs):
        comment_v: Union[str, None] = None
        if "comment" in values:
            comment_v = values.get("comment")
        if v.body is None and comment_v is None:
            raise ValueError("Either comment or body must be specified")
        if v.body is not None and comment_v is not None:
            raise ValueError("Either comment or body must be specified. Not both")
        return v


class AzureClient:
    def __init__(self):
        self.client = EmailClient.from_connection_string(secret_store.AZURE_COMM_CONNECTION_STRING)
        self.from_address = secret_store.AZURE_EMAIL_FROM_ADDRESS

    async def send_email(self, message: MessageResponse):
        if not message.message.body or not message.message.body.content:
            raise Exception("Email body is empty")
        if not message.message.toRecipients:
            raise Exception("No recipient specified")
        try:
            msg = {
                "content": {
                    "subject": message.message.subject,
                    "plainText": "" if message.message.body.contentType == "html" else message.message.body.content,
                    "html": message.message.body.content if message.message.body.contentType == "html" else "",
                },
                "recipients": {
                    "to": list(
                        map(
                            lambda x: {
                                "address": x.emailAddress.address,
                                "displayName": x.emailAddress.name,
                            },
                            message.message.toRecipients,
                        )
                    ),
                    # "cc": [],
                    # "bcc": [],
                },
                "senderAddress": self.from_address,
            }
            poller = self.client.begin_send(msg)
            result = poller.result()
            return result
        except Exception as e:
            print("Failed to send email: " + str(e))
        return False


class OutlookClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.resource_url = "https://graph.microsoft.com"
        self.api_version = "v1.0"
        self.email_endpoint = f"{self.resource_url}/{self.api_version}/me/mailFolders/inbox/messages"
        self.token = None
        self.refresh_token = None
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    async def connect_with_code(self, code: str):
        # Don't authenticate if the code is empty or token is already set
        if not code:
            raise Exception("Authorization failed. Invalid code.")
        if self.token:
            return

        self.token_url = f"https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
            "scope": "Mail.Read Mail.Send",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=token_data) as response:
                token_response = await response.json()
                self.token = token_response.get("access_token")
                self.refresh_token = token_response.get("refresh_token")
                if not self.token:
                    raise Exception("Authorization failed. Invalid code. Message: " + str(token_response))

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    async def connect_with_refresh_token(self, refresh_token: str):
        if not refresh_token:
            raise Exception("Authorization failed. Invalid refersh token.")

        self.token_url = f"https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
        token_data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "refresh_token": refresh_token,
            "scope": "Mail.Read Mail.Send",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=token_data) as response:
                token_response = await response.json()
                self.token = token_response.get("access_token")
                self.refresh_token = token_response.get("refresh_token")
                if not self.token:
                    raise Exception("Authorization failed. Invalid code. Message: " + str(token_response))

    async def reauthenticate(self):
        if not self.refresh_token:
            raise Exception("Refresh token not found.")
        await self.connect_with_refresh_token(self.refresh_token)

    def connect_with_tokens(self, token: str, refresh_token: str):
        self.token = token
        self.refresh_token = refresh_token

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    async def get_user_info(self):
        if not self.token:
            raise Exception("Not connected")

        endpoint_url = f"{self.resource_url}/{self.api_version}/me"
        headers = {"Authorization": f"Bearer {self.token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint_url, headers=headers) as response:
                return await response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    async def reply_email(self, email_id: str, message: MessageResponse):
        if not self.token:
            raise Exception("Not connected")

        endpoint_url = f"{self.resource_url}/{self.api_version}/me/messages/{email_id}/reply"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        email_body = message.dict(exclude_none=True)

        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint_url, headers=headers, json=email_body) as response:
                if response.status >= 200 and response.status < 300:
                    pass
                else:
                    raise Exception(f"{response.status} " + (await response.text()))

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    async def send_email(self, message: MessageResponse):
        if not self.token:
            raise Exception("Not connected")

        endpoint_url = f"{self.resource_url}/{self.api_version}/me/sendMail"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        email_body = message.dict(exclude_none=True)

        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint_url, headers=headers, json=email_body) as response:
                if response.status >= 200 and response.status < 300:
                    pass
                else:
                    raise Exception(f"{response.status} " + (await response.text()))

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    async def receive_email(
        self,
        top: int = 10,
        skip: int = 0,
        order_by: str = "receivedDateTime+DESC",
        received_after: Optional[str] = None,
    ) -> List[dict]:
        if not self.token:
            raise Exception("Not connected")

        query = f"?$top={top}&$skip={skip}&$orderby={order_by}"
        if received_after:
            query += f"&$filter=receivedDateTime gt {received_after}"

        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.email_endpoint}{query}", headers=headers) as response:
                if response.status >= 200 and response.status < 300:
                    email_r = await response.json()
                    if "value" not in email_r:
                        raise Exception("Unexpected response: ", email_r)
                    return email_r.get("value")
                else:
                    raise Exception(f"{response.status} " + (await response.text()))
