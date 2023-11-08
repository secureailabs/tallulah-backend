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


from typing import List, Optional

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


async def read_emails(client: OutlookClient, mailbox_id: PyObjectId):
    try:
        acquire_lock = await Mailboxes.lock(query_mailbox_id=mailbox_id)
        if not acquire_lock:
            print(f"Mailbox {mailbox_id} is already being processed")
            return

        # Get the last refresh time
        mailbox = await Mailboxes.read(mailbox_id=mailbox_id, throw_on_not_found=True)
        last_refresh_time = mailbox[0].last_refresh_time

        # reauthenticate to get the latest token
        await client.reauthenticate()
        top = 100
        skip = 0

        # Fetch the emails
        if last_refresh_time:
            emails = await client.receive_email(top=top, skip=skip, received_after=last_refresh_time)
        else:
            emails = await client.receive_email(top=top, skip=skip)
        skip += top

        if not emails:
            return

        # Update the last refresh time and refresh token
        await Mailboxes.update(
            query_mailbox_id=mailbox_id,
            update_last_refresh_time=emails[0]["receivedDateTime"],
        )

        # Connect to the message queue
        rabbit_mq_connect_url = get_secret("rabbit_mq_host")
        rabbit_mq_queue_name = get_secret("rabbit_mq_queue_name")
        rabbit_mq_client = MessageQueueClient(
            RabbitMQWorkQueue(url=f"{rabbit_mq_connect_url}:5672", queue_name=rabbit_mq_queue_name)
        )
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
                        outlook_id=email["id"],
                        message_state=EmailState.UNPROCESSED,
                    )
                    await Emails.create(email=email_db)

                    # Add the email to the queue for processing
                    await rabbit_mq_client.push_message(str(email_db.id))
                except Exception as exception:
                    print(f"Error: while processing email {email['id']}: {exception}")

            # refetch the next emails
            if last_refresh_time:
                emails = await client.receive_email(top=top, skip=skip, received_after=last_refresh_time)
            else:
                emails = await client.receive_email(top=top, skip=skip)
            skip += top

        # Close the connection to the message queue
        await rabbit_mq_client.disconnect()
    except Exception as exception:
        print(f"Error: while reading emails: {exception}")
    finally:
        # Unlock the mailbox
        await Mailboxes.unlock(query_mailbox_id=mailbox_id)


@router.on_event("startup")
@repeat_every(seconds=3600)  # 1 hour
async def read_emails_hourly():
    print("Reading emails")

    # Get the list of all the mailboxes
    mailboxes = await Mailboxes.read()

    # Add an async task to read emails for each mailbox
    for mailbox in mailboxes:
        # Get the refresh token for the mailbox
        refresh_token = await get_keyvault_secret(str(mailbox.refresh_token_id))
        if not refresh_token:
            print(f"Refresh token not found for mailbox {mailbox.id}")
            continue

        # Connect to the mailbox
        client = OutlookClient(
            client_id=get_secret("outlook_client_id"),
            client_secret=get_secret("outlook_client_secret"),
            redirect_uri=get_secret("outlook_redirect_uri"),
        )
        await client.connect_with_refresh_token(refresh_token)
        if not client.refresh_token:
            print(f"Refresh token not found after authentication for mailbox {mailbox.id}")
            continue

        # update the refresh token secret
        await set_keyvault_secret(str(mailbox.refresh_token_id), client.refresh_token)

        # Add a background task to read emails
        async_task_manager = AsyncTaskManager()
        async_task_manager.create_task(read_emails(client=client, mailbox_id=mailbox.id))


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
    sort_key: str = Query(default="received_time", description="Sort key"),
    sort_direction: int = Query(default=-1, description="Sort direction"),
    filter_tags: Optional[List[str]] = Query(default=None, description="Filter tags"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleEmail_Out:
    # Check if the mailbox belongs to the user
    _ = await Mailboxes.read(mailbox_id=mailbox_id, user_id=current_user.id, throw_on_not_found=True)
    emails = await Emails.read(
        mailbox_id=mailbox_id,
        filter_tags=filter_tags,
        skip=skip,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
        throw_on_not_found=False,
    )
    email_count = await Emails.count(mailbox_id=mailbox_id)

    return GetMultipleEmail_Out(
        messages=[GetEmail_Out(**email.dict()) for email in emails],
        count=email_count,
        next=skip + limit,
        limit=limit,
    )
