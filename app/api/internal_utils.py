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

from fastapi import APIRouter, Response, status
from fastapi.responses import HTMLResponse
from msal import ConfidentialClientApplication

from app.data import operations as data_service
from app.utils.secrets import get_secret

router = APIRouter(tags=["internal"])


@router.delete(
    path="/database",
    description="Drop the database",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="drop_database",
)
async def drop_database() -> Response:
    await data_service.drop()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Create MSAL application instance
app_instance = ConfidentialClientApplication(
    client_id=get_secret("outlook_client_id"),
    authority="https://login.microsoftonline.com/organizations",
    client_credential=get_secret("outlook_client_secret"),
)

# Create OAuth2 Authorization URL
redirect_uri = get_secret("outlook_redirect_uri")
scopes = ["User.Read", "Mail.Read", "Mail.Send"]
authorization_url = app_instance.get_authorization_request_url(scopes=scopes, redirect_uri=redirect_uri)


@router.get("/", response_class=HTMLResponse)
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
