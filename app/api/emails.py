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


from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from fastapi_utils.tasks import repeat_every

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.email import Email_Db, Emails, EmailState, GetEmail_Out, GetMultipleEmail_Out
from app.models.mailbox import Mailbox_Db, Mailboxes
from app.utils.background_couroutines import AsyncTaskManager
from app.utils.emails import EmailBody, Message, MessageResponse, OutlookClient
from app.utils.message_queue import MessageQueueClient, RabbitMQWorkQueue
from app.utils.secrets import get_keyvault_secret, secret_store, set_keyvault_secret

router = APIRouter(prefix="/api/emails", tags=["emails"])


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
        rabbit_mq_connect_url = secret_store.RABBIT_MQ_HOST
        rabbit_mq_queue_name = secret_store.RABBIT_MQ_QUEUE_NAME
        rabbit_mq_client = MessageQueueClient(
            RabbitMQWorkQueue(url=f"{rabbit_mq_connect_url}:5672", queue_name=rabbit_mq_queue_name)
        )
        await rabbit_mq_client.connect()

        while len(emails) > 0:
            for email in emails:
                try:
                    # Create an email object in the database
                    email_db = Email_Db(
                        mailbox_id=mailbox_id,
                        user_id=mailbox[0].user_id,
                        subject=email["subject"],
                        body=email["body"],
                        received_time=email["receivedDateTime"],
                        from_address=email["sender"],
                        outlook_id=email["id"],
                        message_state=EmailState.NEW,
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


async def reply_emails(
    mailbox: Mailbox_Db,
    subject: str,
    reply: EmailBody,
    current_user: TokenData,
    email_ids: Optional[List[PyObjectId]] = None,
    tags: Optional[List[str]] = None,
):
    # store all the outlook ids of the emails as a set
    outlook_ids: Dict[PyObjectId, str] = {}

    # Get the list of all the email_ids
    if email_ids:
        for id in email_ids:
            email = await Emails.read(
                email_id=id, user_id=current_user.id, mailbox_id=mailbox.id, throw_on_not_found=False
            )
            outlook_ids[id] = email[0].outlook_id

    # Get the list of all the emails with tags
    if tags:
        emails = await Emails.read(
            filter_tags=tags, user_id=current_user.id, mailbox_id=mailbox.id, throw_on_not_found=False
        )
        for email in emails:
            outlook_ids[email.id] = email.outlook_id

    # Get the refresh token for the mailbox
    refresh_token = await get_keyvault_secret(str(mailbox.refresh_token_id))
    if not refresh_token:
        print(f"Refresh token not found for mailbox {mailbox.id}")
        raise Exception(f"Refresh token not found for mailbox {mailbox.id}")

    # Connect to the mailbox
    client = OutlookClient(
        client_id=secret_store.OUTLOOK_CLIENT_ID,
        client_secret=secret_store.OUTLOOK_CLIENT_SECRET,
        redirect_uri=secret_store.OUTLOOK_REDIRECT_URI,
    )
    await client.connect_with_refresh_token(refresh_token)
    if not client.refresh_token:
        print(f"Refresh token not found after authentication for mailbox {mailbox.id}")
        raise Exception(f"Refresh token not found after authentication for mailbox {mailbox.id}")

    # update the refresh token secret
    await set_keyvault_secret(str(mailbox.refresh_token_id), client.refresh_token)

    message = MessageResponse(message=Message(subject=subject, body=reply))

    # Reply to all the emails
    for id, outlook_id in outlook_ids.items():
        try:
            await client.reply_email(email_id=outlook_id, message=message)
        except Exception as exception:
            print(f"Error: while replying to email {outlook_id}: {exception}")
            await Emails.update(
                query_message_id=id, update_message_state=EmailState.FAILED, update_message_note=str(exception)
            )
        else:
            await Emails.update(query_message_id=id, update_message_state=EmailState.RESPONDED)


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
            client_id=secret_store.OUTLOOK_CLIENT_ID,
            client_secret=secret_store.OUTLOOK_CLIENT_SECRET,
            redirect_uri=secret_store.OUTLOOK_REDIRECT_URI,
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
    filter_state: Optional[List[EmailState]] = Query(default=None, description="Filter state"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleEmail_Out:
    # Check if the mailbox belongs to the user
    _ = await Mailboxes.read(mailbox_id=mailbox_id, user_id=current_user.id, throw_on_not_found=True)
    emails = await Emails.read(
        mailbox_id=mailbox_id,
        filter_tags=filter_tags,
        filter_state=filter_state,
        skip=skip,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
        throw_on_not_found=False,
    )
    email_count = await Emails.count(
        mailbox_id=mailbox_id,
        filter_tags=filter_tags,
    )

    return GetMultipleEmail_Out(
        messages=[GetEmail_Out(**email.dict()) for email in emails],
        count=email_count,
        next=skip + limit,
        limit=limit,
    )


@router.post(
    path="/replies",
    description="Reply to one email or a tag, or a list of emails or tags",
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="reply_to_emails",
)
async def reply_to_emails(
    mailbox_id: PyObjectId = Query(description="Mailbox id"),
    email_ids: Optional[List[PyObjectId]] = Query(default=None, description="List of email ids"),
    tags: Optional[List[str]] = Query(default=None, description="List of tag ids"),
    subject: str = Body(default=None, description="Subject of the email"),
    reply: EmailBody = Body(default=None, description="Reply to the email"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    if not email_ids and not tags:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No emails or tags provided")

    mailbox = await Mailboxes.read(mailbox_id=mailbox_id, user_id=current_user.id, throw_on_not_found=True)

    async_task_manager = AsyncTaskManager()
    async_task_manager.create_task(reply_emails(mailbox[0], subject, reply, current_user, email_ids, tags))

    return Response(status_code=status.HTTP_202_ACCEPTED)
