# -------------------------------------------------------------------------------
# Tallulah
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


from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi_utils.tasks import repeat_every

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.email import Email_Db, Emails, EmailState, GetEmail_Out, GetMultipleEmail_Out
from app.models.mailbox import Mailboxes
from app.utils.background_couroutines import AsyncTaskManager
from app.utils.emails import OutlookClient
from app.utils.message_queue import MessageQueueClient, RabbitMQWorkQueue
from app.utils.secrets import get_keyvault_secret, get_secret, set_keyvault_secret

router = APIRouter(prefix="/emails", tags=["emails"])


async def read_emails(client: OutlookClient, mailbox_id: PyObjectId, receivedDateTime: Optional[str] = None):
    # reauthenticate to get the latest token
    await client.reauthenticate()

    # Fetch the emails
    if receivedDateTime:
        emails = await client.receive_email(f"$filter=receivedDateTime gt {receivedDateTime}")
    else:
        emails = await client.receive_email()

    if not emails:
        return

    # Update the last refresh time and refresh token
    await Mailboxes.update(
        query_mailbox_id=mailbox_id,
        update_last_refresh_time=emails[0]["receivedDateTime"],
    )

    # Connect to the message queue
    rabbit_mq_connect_url = get_secret("rabbit_mq_host")
    rabbit_mq_client = MessageQueueClient(RabbitMQWorkQueue(url=f"{rabbit_mq_connect_url}:5672"))
    await rabbit_mq_client.connect()

    while emails:
        for email in emails:
            try:
                # Create an email object in the database
                email_db = Email_Db(
                    mailbox_id=mailbox_id,
                    subject=email["subject"],
                    body=email["body"],
                    received_time=email["receivedDateTime"],
                    from_address=email["sender"],
                    message_state=EmailState.UNPROCESSED,
                )
                await Emails.create(email=email_db)

                # Add the email to the queue for processing
                await rabbit_mq_client.push_message(str(email_db.id))
            except Exception as exception:
                print(f"Error: while processing email {email['id']}: {exception}")

        # refetch the next emails
        emails = await client.receive_email()

    # Close the connection to the message queue
    await rabbit_mq_client.disconnect()


@router.on_event("startup")
@repeat_every(seconds=3600)  # 1 hour
async def read_emails_hourly():
    print("Reading emails")

    # Get the list of all the mailboxes
    mailboxes = await Mailboxes.read()

    # Add an async task to read emails for each mailbox
    for mailbox in mailboxes:
        # Don't read emails for mailboxes where last_refresh_time is less than 1 hour
        if mailbox.last_refresh_time and datetime.strptime(
            mailbox.last_refresh_time, "%Y-%m-%dT%H:%M:%SZ"
        ) > datetime.utcnow() - timedelta(hours=1):
            continue

        # Get the refresh token for the mailbox
        refresh_token = await get_keyvault_secret(str(mailbox.refresh_token_id))
        if not refresh_token:
            print(f"Refresh token not found for mailbox {mailbox.id}")
            continue

        # Connect to the mailbox
        client = OutlookClient()
        await client.connect_with_refresh_token(refresh_token)
        if not client.refresh_token:
            print(f"Refresh token not found after authentication for mailbox {mailbox.id}")
            continue

        # update the refresh token secret
        await set_keyvault_secret(str(mailbox.refresh_token_id), client.refresh_token)

        # Add a background task to read emails
        async_task_manager = AsyncTaskManager()
        async_task_manager.create_task(
            read_emails(client=client, mailbox_id=mailbox.id, receivedDateTime=mailbox.last_refresh_time)
        )

    print("Done reading emails")


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
    email_count = await Emails.count(mailbox_id=mailbox_id)

    return GetMultipleEmail_Out(
        messages=[GetEmail_Out(**email.dict()) for email in emails],
        count=email_count,
        next=skip + limit,
        limit=limit,
    )
