# -------------------------------------------------------------------------------
# Engineering
# mailbox.py
# -------------------------------------------------------------------------------
""" Service to read emails from user account """
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Secure Ai Labs, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Secure Ai Labs, Inc.
# -------------------------------------------------------------------------------


from fastapi import APIRouter, Query, Response, status
from fastapi.encoders import jsonable_encoder

from app.models.common import PyObjectId
from app.models.mailbox import Message_Db, Messages, MessageType
from app.utils.background_couroutines import add_async_task
from app.utils.emails import EmailService, OutlookClient

router = APIRouter(prefix="/mailbox", tags=["mailbox"])


@router.get(
    path="/authorize/",
    description="Authorize the user by sending the OAuth code",
    status_code=status.HTTP_200_OK,
    operation_id="outlook_authorize",
)
async def outlook_authorize(
    code: str = Query(description="OAuth code"),
    session_state: str = Query(description="Session state id"),
) -> Response:
    # Add a background task to read emails
    add_async_task(read_emails(code, PyObjectId()))

    return Response(status_code=status.HTTP_200_OK)


async def read_emails(code: str, source_id: PyObjectId):
    client = OutlookClient(code)
    email_service = EmailService(client)
    emails = await email_service.receive_email("")

    for email in emails:
        # Create an email object in the database
        message_db = Message_Db(source_id=source_id, message_type=MessageType.EMAIL, message=jsonable_encoder(email))
        await Messages.create(message=message_db)

        # Add the email to the queue for processing
