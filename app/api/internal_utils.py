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

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import HTMLResponse
from msal import ConfidentialClientApplication

from app.api.accounts import add_tallulah_admin
from app.api.authentication import RoleChecker, get_current_user
from app.data.operations import DatabaseOperations
from app.models.authentication import TokenData
from app.utils.secrets import secret_store

router = APIRouter(tags=["internal"])

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


@router.get("/api/", response_class=HTMLResponse)
async def read_root():
    html_content = f"""
    <html>
        <head>
            <title>Login with Microsoft</title>
        </head>
        <body>
            <a href="{authorization_url}"><button>Login with Microsoft</button></a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
