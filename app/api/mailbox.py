# -------------------------------------------------------------------------------
# Engineering
# mailbox.py
# -------------------------------------------------------------------------------
""" Service to read emails from user account """
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------


from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response, status

from app.api.authentication import get_current_user
from app.api.emails import read_emails
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.email import Emails
from app.models.mailbox import (
    GetMailbox_Out,
    GetMultipleMailboxes_Out,
    Mailbox_Db,
    Mailboxes,
    MailboxProvider,
    MailboxState,
    RegisterMailbox_In,
    RegisterMailbox_Out,
)
from app.utils.background_couroutines import AsyncTaskManager
from app.utils.emails import OutlookClient
from app.utils.secrets import delete_keyvault_secret, secret_store, set_keyvault_secret

router = APIRouter(prefix="/api/mailbox", tags=["mailbox"])


@router.post(
    path="/",
    description="Add a new mailbox by code",
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="add_new_mailbox",
)
async def add_new_mailbox(
    mailbox_info: RegisterMailbox_In = Body(
        description="Oauth code that is used to fetch the token from the authorization server"
    ),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterMailbox_Out:
    # Connect to the mailbox and check if the user is valid
    try:
        client = None
        if mailbox_info.provider == MailboxProvider.OUTLOOK:
            client = OutlookClient(
                client_id=secret_store.OUTLOOK_CLIENT_ID,
                client_secret=secret_store.OUTLOOK_CLIENT_SECRET,
                redirect_uri=secret_store.OUTLOOK_REDIRECT_URI,
            )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mailbox provider")

        await client.connect_with_code(mailbox_info.code)
        user_info = await client.get_user_info()

    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exception))

    if not client.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token not found. Mailbox addition failed."
        )

    # Add the refresh token to the keyvault
    refresh_token_id = PyObjectId()
    await set_keyvault_secret(str(refresh_token_id), client.refresh_token)

    mailbox_db = Mailbox_Db(
        email=user_info["mail"],
        user_id=current_user.id,
        refresh_token_id=refresh_token_id,
        state=MailboxState.IDLE,
    )
    await Mailboxes.create(mailbox=mailbox_db)

    # Add a background task to read emails
    # background_tasks.add_task(read_emails, client, mailbox_db.id, None)
    async_task_manager = AsyncTaskManager()
    async_task_manager.create_task(read_emails(client, mailbox_db.id))

    return RegisterMailbox_Out(_id=mailbox_db.id)


@router.get(
    path="/",
    description="Get all the mailboxes for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_all_mailboxes",
)
async def get_all_mailboxes(
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleMailboxes_Out:
    mailboxes = await Mailboxes.read(user_id=current_user.id, throw_on_not_found=False)

    return GetMultipleMailboxes_Out(mailboxes=[GetMailbox_Out(**mailbox.dict()) for mailbox in mailboxes])


@router.get(
    path="/{mailbox_id}",
    description="Get the mailbox for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_mailbox",
)
async def get_mailbox(
    mailbox_id: PyObjectId = Path(description="Mailbox id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMailbox_Out:
    mailboxe = await Mailboxes.read(mailbox_id=mailbox_id, user_id=current_user.id, throw_on_not_found=True)

    return GetMailbox_Out(**mailboxe[0].dict())


@router.delete(
    path="/{mailbox_id}",
    description="Delete the mailbox and all the emails for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_mailbox",
)
async def delete_mailbox(
    mailbox_id: PyObjectId = Path(description="Mailbox id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Get the mailbox information
    mailbox = await Mailboxes.read(mailbox_id=mailbox_id, user_id=current_user.id, throw_on_not_found=True)

    # Delete the mailbox
    await Mailboxes.delete(query_mailbox_id=mailbox_id, user_id=current_user.id)

    # Delete all the emails associated with the mailbox
    await Emails.delete(mailbox_id=mailbox_id)

    # Delete the refresh token from the keyvault
    await delete_keyvault_secret(str(mailbox[0].refresh_token_id))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
