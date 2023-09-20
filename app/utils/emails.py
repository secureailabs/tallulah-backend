import email
import imaplib
from abc import ABC, abstractmethod
from email.header import decode_header
from typing import List

import aiohttp


class EmailServiceProvider(ABC):
    @abstractmethod
    def send_email(self, email_address, message):
        pass

    @abstractmethod
    def receive_email(self, query) -> List[dict]:
        pass


class ImapClient(EmailServiceProvider):
    def __init__(self, username: str, password: str, host: str, port: int = 993):
        self.client = imaplib.IMAP4_SSL(host, port)
        self.client.login(username, password)
        self.client.select("inbox")

    def send_email(self, email_address: str, message: str):
        raise NotImplementedError

    def receive_email(self, query: str):
        # Search for all unread messages
        status, messages = self.client.search(None, "(UNSEEN)")
        if status == "OK":
            # Convert messages to a list of email IDs
            email_ids = messages[0].split()

            # Iterate over the email IDs to fetch the email content
            for e_id in email_ids:
                _, msg_data = self.client.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        # Parse the email content into a message object
                        msg = email.message_from_bytes(response_part[1])

                        # Decode the email subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            if encoding:
                                subject = subject.decode(encoding)
                            else:
                                subject = subject.decode("utf-8")

                        # Get the email sender
                        from_ = msg.get("From")
                        print("From:", from_)
                        print("Subject:", subject)
                        print("\n" + "-" * 50 + "\n")

                        # If the email message is multipart
                        if msg.is_multipart():
                            # Iterate over email parts
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                try:
                                    # Get the email body
                                    body = part.get_payload(decode=True).decode()
                                    if content_type == "text/plain" and "attachment" not in content_disposition:
                                        print(body)
                                except:
                                    pass
                        else:
                            # Get the email body
                            body = msg.get_payload(decode=True).decode()
                            print(body)
                        print("\n" + "-" * 50 + "\n")

        def __del__(self):
            self.client.logout()


class OutlookClient(EmailServiceProvider):
    async def __init__(self, code: str):
        CLIENT_ID = "5f247444-fff8-42b2-9362-1d2fe5246de1"
        REDIRECT_URI = "https://127.0.0.1:8000/authorize"
        AUTHORITY_URL = "https://login.microsoftonline.com/organizations"
        self.RESOURCE_URL = "https://graph.microsoft.com"
        self.API_VERSION = "v1.0"
        SCOPES = "Mail.Read"

        token_url = f"https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
        token_data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "scope": SCOPES,
        }

        # Make an async request to get the access token
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=token_data) as response:
                self.token = (await response.json()).get("access_token")

    def send_email(self, email_address: List[str], message: str):
        raise NotImplementedError

    async def receive_email(self, query: str):
        endpoint_url = f"{self.RESOURCE_URL}/{self.API_VERSION}/me/messages"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint_url, headers=headers) as response:
                email_r = await response.json()
                emails = email_r.get("value")
                return emails

    def __del__(self):
        pass


class EmailService:
    def __init__(self, email_service: EmailServiceProvider):
        self.email_service = email_service

    async def send_email(self, email_address, message):
        return self.email_service.send_email(email_address, message)

    async def receive_email(self, query):
        return self.email_service.receive_email(query)
