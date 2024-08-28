# -------------------------------------------------------------------------------
# Engineering
# internal_utils.py
# -------------------------------------------------------------------------------
"""SAIL internal util API functionses"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------


import aiohttp
from fastapi import APIRouter, Body, Response, status
from msal import ConfidentialClientApplication

from app.models.common import SailBaseModel
from app.utils.secrets import secret_store

router = APIRouter(tags=["web-utils"])

# Create MSAL application instance
app_instance = ConfidentialClientApplication(
    client_id=secret_store.OUTLOOK_CLIENT_ID,
    authority="https://login.microsoftonline.com/organizations",
    client_credential=secret_store.OUTLOOK_CLIENT_SECRET,
)
# Create OAuth2 Authorization URL
redirect_uri = secret_store.OUTLOOK_REDIRECT_URI
scopes = ["User.Read", "Mail.Read", "Mail.Send"]
authorization_url = app_instance.get_authorization_request_url(scopes=scopes, redirect_uri=redirect_uri)


class CaptchaRequest(SailBaseModel):
    captchaToken: str


@router.post(
    path="/api/verify-captcha",
    description="Verify captcha token",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="verify_captcha",
)
async def verify_captcha(
    captcha_req: CaptchaRequest = Body(description="Captcha token"),
) -> Response:
    captcha_token = captcha_req.captchaToken
    secret_key = secret_store.GOOGLE_RECAPTCHA_SECRET_KEY

    verification_url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {"secret": secret_key, "response": captcha_token}

    async with aiohttp.ClientSession() as session:
        async with session.post(verification_url, data=payload) as response:
            response = await response.json()
            if response["success"]:
                return Response(status_code=status.HTTP_202_ACCEPTED, content="Captcha verification successful")
            else:
                return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Captcha verification failed")
