# -------------------------------------------------------------------------------
# Engineering
# emails.py
# -------------------------------------------------------------------------------
""" Service to manage emails from user account """
# -------------------------------------------------------------------------------
# Copyright (C) 2023 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------


from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Path, Query, Response, status

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.email import Email_Db, Emails, EmailState, GetEmail_Out, GetMultipleEmail_Out
from app.models.mailbox import Mailboxes
from app.utils.emails import EmailService, OutlookClient
from app.utils.message_queue import MessageQueueClient, RabbitMQWorkQueue
from app.utils.secrets import get_secret

router = APIRouter(prefix="/emails", tags=["emails"])


async def read_emails(client: OutlookClient, mailbox_id: PyObjectId):
    email_service = EmailService(client)
    emails = await email_service.receive_email("")

    # Connect to the message queue
    rabbit_mq_connect_url = get_secret("rabbit_mq_host")
    rabbit_mq_client = MessageQueueClient(RabbitMQWorkQueue(url=f"{rabbit_mq_connect_url}:5672"))
    await rabbit_mq_client.connect()

    while emails:
        for email in emails:
            # Create an email object in the database
            email_db = Email_Db(
                mailbox_id=mailbox_id,
                subject=email["subject"],
                body=email["body"],
                received_time=email["received_time"],
                message_state=EmailState.UNPROCESSED,
            )
            await Emails.create(email=email_db)

            # Add the email to the queue for processing
            await rabbit_mq_client.push_message(str(email))

        # refetch the next emails
        emails = await email_service.receive_email("")

    await rabbit_mq_client.disconnect()


@router.get(
    path="/",
    description="Get all the emails from the mailbox",
    status_code=status.HTTP_200_OK,
    operation_id="get_all_emails",
)
async def get_all_emails(
    mailbox_id: PyObjectId = Query(description="Mailbox id"),
    skip: int = Query(default=0, description="Number of emails to skip"),
    limit: int = Query(default=20, description="Number of emails to return"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleEmail_Out:
    # Check if the mailbox belongs to the user
    _ = await Mailboxes.read(mailbox_id=mailbox_id, user_id=current_user.id, throw_on_not_found=True)

    emails = await Emails.read(mailbox_id=mailbox_id, skip=skip, limit=limit, throw_on_not_found=False)

    return GetMultipleEmail_Out(
        messages=[GetEmail_Out(**email.dict()) for email in emails], next=skip + limit, limit=limit
    )
