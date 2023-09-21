import email
import imaplib
from abc import ABC, abstractmethod
from email.header import decode_header
from typing import List

import aiohttp


class EmailServiceProvider(ABC):
    @abstractmethod
    async def send_email(self, email_address, message):
        pass

    @abstractmethod
    async def receive_email(self, query) -> List[dict]:
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
    def __init__(self, code: str):
        CLIENT_ID = "5f247444-fff8-42b2-9362-1d2fe5246de1"
        REDIRECT_URI = "https://127.0.0.1:8000/authorize"
        AUTHORITY_URL = "https://login.microsoftonline.com/organizations"
        self.RESOURCE_URL = "https://graph.microsoft.com"
        self.API_VERSION = "v1.0"
        SCOPES = "Mail.Read Mail.Send"

        self.token_url = f"https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
        self.token_data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "scope": SCOPES,
        }

    async def connect(self):
        # Make an async request to get the access token
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=self.token_data) as response:
                self.token = (await response.json()).get("access_token")

    async def get_user_info(self):
        if not self.token:
            raise Exception("Not connected")

        endpoint_url = f"{self.RESOURCE_URL}/{self.API_VERSION}/me"
        headers = {"Authorization": f"Bearer {self.token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint_url, headers=headers) as response:
                return await response.json()

    async def send_email(self, email_address: List[str], subject: str, message: str):
        if not self.token:
            raise Exception("Not connected")

        endpoint_url = f"{self.RESOURCE_URL}/{self.API_VERSION}/me/sendMail"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        email_body = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": message},
                "toRecipients": [{"emailAddress": {"address": email_address[0]}}],
            },
            "saveToSentItems": "true",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint_url, headers=headers, json=email_body) as response:
                return await response.json()

    async def receive_email(self, query: str):
        if not self.token:
            raise Exception("Not connected")

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

    async def send_email(self, email_address, subject, message):
        return await self.email_service.send_email(email_address, message)

    async def receive_email(self, query):
        return await self.email_service.receive_email(query)


async def main():
    code = "0.AXwA7-V0Pmp-8EyFc2gMpJtk2ER0JF_4_7JCk2IdL-UkbeF8AGg.AgABAAIAAAAtyolDObpQQ5VtlI4uGjEPAgDs_wUA9P8Dl2Js8TkH8umTq8wvQTIG3xVDWBT0inWYrfN6h6yZ8kkfSvj0H9Q_r2OTdMPzgZK0x6_oROFUe4K8Lg57yE_ICDoi_zBMMp-Vm4nmLU3nvXMDqLNFlgHKQdTSsj4-UL-vhAcVblM6dnYpcw7hLvLm8dQcI0eB-C2DU-ER3uXDgVY9FNKR6frvKAmGmNz0B0P4KC9bMkKhrEH6uO2dmyGdgQFPI_VZ994WV8ftDrxq9XcoAtRPHtu7yH3tXk-uVpEVCt37l7k8gaMqsz1jnmuZCMA6OGlGgnRRDCsr5cf7f_Z6sD3Dobiu-xKqMYVH-fw-c4kFp6WQVW2UB0wYWAGypxNxeGNW-2T3GE0Fuf2-ooxCuDZJJB89LtKZNhbWm5tYLmOy4p4JYunFQcfnCEaB6pe5zjVcXGrGLPDhG-n_dsg2zpzhtwVe6PVDykLveBcUKTYaR4APORPDJXYzN94Ibb9pCwQTZpmHGV4-mDzvrHoepExjMf_gKwitT_1lV9luTun4RL-C-UZnJAyrN8LBYuBeYrJBFadZ6QkzYY7Fw7392tzJsXtlkp6DmHsXjxv8r6sGWu4Zt0ALOZE3UuhrEkml3vF1EIyDlrxgcxiX3HqeRPUvrlymDdEPgcqA-GR4vZXAV2UfJFH4eQHZLhwLH8g46_ZNqVipx5SP4Cd3a90tFF2wa2T7cLsajmBLLKBaPB9srLROc07iBibTPdx1c4AIxJRwGiHi9g1gKx6IKIlNHWYp5iOigadQKAVB9MzxG9ws_T0L0Cdag6iWsyG1cmRBqfw"
    outlook_client = OutlookClient(code)
    await outlook_client.connect()
    user_info = await outlook_client.get_user_info()
    print(user_info)
    email_service = EmailService(outlook_client)
    emails = await email_service.receive_email("")
    print(emails)
    send_resp = await email_service.send_email(
        ["prawal@secureailabs.com"], "Test email from Python", "Hello this is prawal"
    )
    print(send_resp)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
