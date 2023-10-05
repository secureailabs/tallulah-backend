import email
import imaplib
from abc import ABC, abstractmethod
from email.header import decode_header
from typing import List, Optional

import aiohttp

from app.utils.secrets import get_secret


class EmailServiceProvider(ABC):
    @abstractmethod
    async def send_email(self, email_address, subject, message):
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
    def __init__(self):
        self.resource_url = "https://graph.microsoft.com"
        self.api_version = "v1.0"
        self.base_email_endpoint = f"{self.resource_url}/{self.api_version}/me/mailFolders/inbox/messages"
        self.current_email_endpoint = f"{self.resource_url}/{self.api_version}/me/mailFolders/inbox/messages"
        self.token = None
        self.refresh_token = None

    async def connect_with_code(self, code: str):
        # Don't authenticate if the code is empty or token is already set
        if not code:
            raise Exception("Authorization failed. Invalid code.")
        if self.token:
            return

        self.token_url = f"https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
        token_data = {
            "grant_type": "authorization_code",
            "client_id": get_secret("outlook_client_id"),
            "client_secret": get_secret("outlook_client_secret"),
            "redirect_uri": get_secret("outlook_redirect_uri"),
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

    async def connect_with_refresh_token(self, refresh_token: str):
        if not refresh_token:
            raise Exception("Authorization failed. Invalid refersh token.")

        self.token_url = f"https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
        token_data = {
            "grant_type": "refresh_token",
            "client_id": get_secret("outlook_client_id"),
            "client_secret": get_secret("outlook_client_secret"),
            "redirect_uri": get_secret("outlook_redirect_uri"),
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

    async def get_user_info(self):
        if not self.token:
            raise Exception("Not connected")

        endpoint_url = f"{self.resource_url}/{self.api_version}/me"
        headers = {"Authorization": f"Bearer {self.token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint_url, headers=headers) as response:
                return await response.json()

    async def send_email(self, email_address: List[str], subject: str, message: str):
        if not self.token:
            raise Exception("Not connected")

        endpoint_url = f"{self.resource_url}/{self.api_version}/me/sendMail"
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
                return await response.text()

    async def receive_email(self, query: Optional[str] = None):
        if query:
            self.current_email_endpoint = f"{self.base_email_endpoint}?{query}"

        if not self.token:
            raise Exception("Not connected")

        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(self.current_email_endpoint, headers=headers) as response:
                email_r = await response.json()
                emails = email_r.get("value")
                self.current_email_endpoint = email_r.get("@odata.nextLink")
                return emails

    def __del__(self):
        pass


async def test():
    import webbrowser

    client_id = get_secret("outlook_client_id")
    redirect_uri = get_secret("outlook_redirect_uri")
    scope = "openid offline_access User.Read Mail.Read Mail.Send"
    auth_url = f"https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}&response_mode=query"
    webbrowser.open(auth_url)

    code = input("Enter the code from the address bar in the browser: ")
    # Sample value of code that is required as an input
    # code = "0.AXwA7-V0Pmp-8EyFc2gMpJtk2ER0JF_4_7JCk2IdL-UkbeF8AGg.AgABAAIAAAAtyolDObpQQ5VtlI4uGjEPAgDs_wUA9P8Dl2Js8TkH8umTq8wvQTIG3xVDWBT0inWYrfN6h6yZ8kkfSvj0H9Q_r2OTdMPzgZK0x6_oROFUe4K8Lg57yE_ICDoi_zBMMp-Vm4nmLU3nvXMDqLNFlgHKQdTSsj4-UL-vhAcVblM6dnYpcw7hLvLm8dQcI0eB-C2DU-ER3uXDgVY9FNKR6frvKAmGmNz0B0P4KC9bMkKhrEH6uO2dmyGdgQFPI_VZ994WV8ftDrxq9XcoAtRPHtu7yH3tXk-uVpEVCt37l7k8gaMqsz1jnmuZCMA6OGlGgnRRDCsr5cf7f_Z6sD3Dobiu-xKqMYVH-fw-c4kFp6WQVW2UB0wYWAGypxNxeGNW-2T3GE0Fuf2-ooxCuDZJJB89LtKZNhbWm5tYLmOy4p4JYunFQcfnCEaB6pe5zjVcXGrGLPDhG-n_dsg2zpzhtwVe6PVDykLveBcUKTYaR4APORPDJXYzN94Ibb9pCwQTZpmHGV4-mDzvrHoepExjMf_gKwitT_1lV9luTun4RL-C-UZnJAyrN8LBYuBeYrJBFadZ6QkzYY7Fw7392tzJsXtlkp6DmHsXjxv8r6sGWu4Zt0ALOZE3UuhrEkml3vF1EIyDlrxgcxiX3HqeRPUvrlymDdEPgcqA-GR4vZXAV2UfJFH4eQHZLhwLH8g46_ZNqVipx5SP4Cd3a90tFF2wa2T7cLsajmBLLKBaPB9srLROc07iBibTPdx1c4AIxJRwGiHi9g1gKx6IKIlNHWYp5iOigadQKAVB9MzxG9ws_T0L0Cdag6iWsyG1cmRBqfw"

    outlook_client = OutlookClient()
    await outlook_client.connect_with_code(code)
    user_info = await outlook_client.get_user_info()
    print(user_info)
    email_service = outlook_client
    emails = await email_service.receive_email("")
    print([email["subject"] for email in emails])
    emails = await email_service.receive_email("")
    print([email["subject"] for email in emails])
    send_resp = await email_service.send_email(
        ["prawal@secureailabs.com"], "Test email from Python", "Hello this is prawal"
    )
    print(send_resp)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test())
