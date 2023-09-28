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

from app.models.mailbox import GetMessage_Out, GetMultipleMessage_Out, Message_Db, Messages, MessageType
from app.utils.background_couroutines import add_async_task
from app.utils.emails import EmailService, OutlookClient
from app.utils.message_queue import MessageQueueClient, RabbitMQWorkQueue
from app.utils.secrets import get_secret

router = APIRouter(prefix="/mailbox", tags=["mailbox"])


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
    # Add a background task to read emails
    add_async_task(read_emails(code))

    return Response(status_code=status.HTTP_200_OK)


async def read_emails(code: str):
    client = OutlookClient(code)
    await client.connect()
    user_info = await client.get_user_info()
    email_service = EmailService(client)
    emails = await email_service.receive_email("")

    # Connect to the message queue
    rabbit_mq_connect_url = get_secret("rabbit_mq_host")
    rabbit_mq_client = MessageQueueClient(RabbitMQWorkQueue(url=f"{rabbit_mq_connect_url}:5672"))
    await rabbit_mq_client.connect()

    for email in emails:
        # Create an email object in the database
        message_db = Message_Db(
            source=user_info["mail"],
            message_type=MessageType.EMAIL,
            message=str({"subject": email["subject"], "body": email["body"]["content"]}),
        )
        await Messages.create(message=message_db)

        # Add the email to the queue for processing
        await rabbit_mq_client.push_message(str(email))

    await rabbit_mq_client.disconnect()


@router.get(
    path="/",
    description="Authorize the user by sending the OAuth code",
    status_code=status.HTTP_200_OK,
    operation_id="get_emails",
)
async def get_emails() -> GetMultipleMessage_Out:
    # Add a background task to read emails
    all_emails = await Messages.read(throw_on_not_found=False)

    return GetMultipleMessage_Out(messages=[GetMessage_Out(**email.dict()) for email in all_emails])
