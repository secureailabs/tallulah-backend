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


from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Path, Query, Response, status

from app.api.authentication import get_current_user
from app.api.emails import read_emails
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.mailbox import (
    GetMailbox_Out,
    GetMultipleMailboxes_Out,
    Mailbox_Db,
    Mailboxes,
    MailboxProvider,
    RegisterMailbox_In,
    RegisterMailbox_Out,
)
from app.utils.emails import OutlookClient

router = APIRouter(prefix="/mailbox", tags=["mailbox"])


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
    background_tasks: BackgroundTasks = Depends(),
) -> RegisterMailbox_Out:
    # Connect to the mailbox and check if the user is valid
    try:
        client = None
        if mailbox_info.provider == MailboxProvider.OUTLOOK:
            client = OutlookClient(mailbox_info.code)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mailbox provider")

        await client.connect()
        user_info = await client.get_user_info()

    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exception))

    mailbox_db = Mailbox_Db(email=user_info["mail"], user_id=current_user.id)
    await Mailboxes.create(mailbox=mailbox_db)

    # Add a background task to read emails
    background_tasks.add_task(read_emails, client, mailbox_db.id)

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

    return GetMultipleMailboxes_Out(messages=[GetMailbox_Out(**email.dict()) for email in mailboxes])


@router.get(
    path="/{mailbox_id}",
    description="Get the mailbox for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_mailboxe",
)
async def get_all_mailboxe(
    mailbox_id: PyObjectId = Path(description="Mailbox id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMailbox_Out:
    mailboxe = await Mailboxes.read(mailbox_id=mailbox_id, user_id=current_user.id, throw_on_not_found=True)

    return GetMailbox_Out(**mailboxe[0].dict())


@router.get(
    path="/authorize",
    description="Authorize the user by sending the OAuth code",
    status_code=status.HTTP_200_OK,
    operation_id="outlook_authorize",
)
async def outlook_authorize(
    code: str = Query(description="OAuth code"),
    session_state: str = Query(description="Session state id"),
) -> Response:
    return Response(status_code=status.HTTP_200_OK)
