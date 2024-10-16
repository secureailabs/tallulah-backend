from app.models.common import PyObjectId
from app.models.email import Email_Db, Emails, EmailState
from app.models.mailbox import Mailboxes
from app.utils import log_manager
from app.utils.background_couroutines import AsyncTaskManager
from app.utils.emails import OutlookClient
from app.utils.lock_store import RedisLockStore
from app.utils.message_queue import MessageQueueTypes, RabbitMQWorkQueue
from app.utils.secrets import get_keyvault_secret, secret_store, set_keyvault_secret


async def read_emails(client: OutlookClient, mailbox_id: PyObjectId):
    acquire_lock = False
    try:
        # Acquire a lock on the mailbox for 1 hour max
        lock_store = RedisLockStore()
        acquire_lock = await lock_store.acquire(f"mailbox_{str(mailbox_id)}", expiry=60 * 60)
        if not acquire_lock:
            log_manager.INFO({"message": f"Mailbox {mailbox_id} is already being processed"})
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
        rabbit_mq_client = RabbitMQWorkQueue(
            connection_string=f"{rabbit_mq_connect_url}:5672", queue_name=MessageQueueTypes.EMAIL_QUEUE
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
                    log_manager.INFO({"message": f"Error: while processing email {email['id']}: {exception}"})

            # refetch the next emails
            if last_refresh_time:
                emails = await client.receive_email(top=top, skip=skip, received_after=last_refresh_time)
            else:
                emails = await client.receive_email(top=top, skip=skip)
            skip += top

        # Close the connection to the message queue
        await rabbit_mq_client.disconnect()
    except Exception as exception:
        log_manager.INFO({"message": f"Error: while reading emails: {exception}"})
    finally:
        # Unlock the mailbox after processing
        if acquire_lock:
            await lock_store.release(f"mailbox_{str(mailbox_id)}")


async def read_all_mailboxes():
    # Get the list of all the mailboxes
    mailboxes = await Mailboxes.read()

    # Add an async task to read emails for each mailbox
    for mailbox in mailboxes:
        # Get the refresh token for the mailbox
        refresh_token = await get_keyvault_secret(str(mailbox.refresh_token_id))
        if not refresh_token:
            log_manager.INFO({"message": f"Refresh token not found for mailbox {mailbox.id}"})
            continue

        # Connect to the mailbox
        client = OutlookClient(
            client_id=secret_store.OUTLOOK_CLIENT_ID,
            client_secret=secret_store.OUTLOOK_CLIENT_SECRET,
            redirect_uri=secret_store.OUTLOOK_REDIRECT_URI,
        )
        await client.connect_with_refresh_token(refresh_token)
        if not client.refresh_token:
            log_manager.INFO({"message": f"Refresh token not found after authentication for mailbox {mailbox.id}"})
            continue

        # update the refresh token secret
        await set_keyvault_secret(str(mailbox.refresh_token_id), client.refresh_token)

        # Add a background task to read emails
        async_task_manager = AsyncTaskManager()
        async_task_manager.create_task(read_emails(client=client, mailbox_id=mailbox.id))
