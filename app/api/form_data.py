# -------------------------------------------------------------------------------
# Engineering
# form_data.py
# -------------------------------------------------------------------------------
""" Service to manage form datas """
# -------------------------------------------------------------------------------
# Copyright (C) 2023 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------


import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Path, Query, Response, status
from fastapi.encoders import jsonable_encoder
from openai import organization

from app.api.authentication import RoleChecker, get_current_user
from app.models.accounts import Users
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.form_data import (
    FormData_Db,
    FormDatas,
    FormDataState,
    FormFilter_In,
    GetFormData_Out,
    GetFormDataLocation_Out,
    GetMultipleFormData_Out,
    RegisterFormData_In,
    RegisterFormData_Out,
    UpdateFormData_In,
)
from app.models.form_templates import FormMediaTypes, FormTemplates, GetStorageUrl_Out
from app.utils import log_manager
from app.utils.azure_blob_manager import AzureBlobManager
from app.utils.azure_openai import OpenAiGenerator
from app.utils.background_couroutines import AsyncTaskManager
from app.utils.elastic_search import ElasticsearchClient
from app.utils.emails import EmailAddress, EmailBody, Message, MessageResponse, OutlookClient, ToRecipient
from app.utils.lock_store import RedisLockStore
from app.utils.message_queue import MessageQueueTypes, RabbitMQProducerConsumer
from app.utils.secrets import secret_store
from dateutil.parser import parse as parse_date

router = APIRouter(prefix="/api/form-data", tags=["form-data"])

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_fields(values: dict):
    try:
        for key, field in values.items():
            if field["type"].lower() == "date":
                if not field["value"]:
                    field["value"] = None
                else:
                    try:
                        # Attempt to parse the date string
                        field["value"] = parse_date(field["value"]).isoformat()
                    except ValueError:
                        field["value"] = None
    except Exception as e:
        logger.error(f"Error cleaning fields: {e}")
    # print(f"Cleaned values: {values}")
    return values


async def queue_form_data_metadata_generation():
    log_manager.DEBUG({"message": "Pushing a message to the task queue to generate structured data"})

    # Get the form data for which the metadata is not yet generated
    metadata_not_generated = await FormDatas.read(field_not_exists="metadata")
    if not metadata_not_generated:
        return

    for form_data in metadata_not_generated:
        form_data_id = form_data.id

        lock_store = RedisLockStore()
        is_locked = await lock_store.is_locked(f"form_data_{str(form_data_id)}")
        if is_locked:
            log_manager.INFO({"message": f"Form data {form_data_id} is already being processed"})
            continue

        log_manager.DEBUG(
            {"message": f"Pushing a message {form_data_id} to the task queue to generate structured data"}
        )
        task_queue = RabbitMQProducerConsumer(
            queue_name=MessageQueueTypes.FORM_DATA_METADATA_GENERATION,
            connection_string=f"{secret_store.RABBIT_MQ_HOST}:5672",
        )
        await task_queue.connect()
        await task_queue.push_message(str(form_data_id))

        # sleep for 10 seconds to avoid rate limiting
        await asyncio.sleep(10)


async def queue_all_form_data_metadata_generation():
    log_manager.DEBUG({"message": "Pushing a message to the task queue to generate structured data"})

    # Get all the form data
    metadata_not_generated = await FormDatas.read()
    if not metadata_not_generated:
        return

    for form_data in metadata_not_generated:
        form_data_id = form_data.id

        lock_store = RedisLockStore()
        is_locked = await lock_store.is_locked(f"form_data_{str(form_data_id)}")
        if is_locked:
            log_manager.INFO({"message": f"Form data {form_data_id} is already being processed"})
            continue

        log_manager.DEBUG(
            {"message": f"Pushing a message {form_data_id} to the task queue to generate structured data"}
        )
        task_queue = RabbitMQProducerConsumer(
            queue_name=MessageQueueTypes.FORM_DATA_METADATA_GENERATION,
            connection_string=f"{secret_store.RABBIT_MQ_HOST}:5672",
        )
        await task_queue.connect()
        await task_queue.push_message(str(form_data_id))

        # sleep for 10 seconds to avoid rate limiting
        await asyncio.sleep(10)


async def notify_users(form_template_id: PyObjectId):
    # Get the form template
    try:
        form_template = await FormTemplates.read(template_id=form_template_id, throw_on_not_found=True)
        form_template = form_template[0]

        if not form_template.email_subscription:
            return

        # Connect to the outlook client
        client = OutlookClient(
            client_id=secret_store.OUTLOOK_CLIENT_ID,
            client_secret=secret_store.OUTLOOK_CLIENT_SECRET,
            redirect_uri=secret_store.OUTLOOK_REDIRECT_URI,
        )
        await client.connect_with_refresh_token(secret_store.EMAIL_NO_REPLY_REFRESH_TOKEN)

        # Send email notifications to the subscribed users
        for user_id in form_template.email_subscription:
            # Get the user email
            user = await Users.read(user_id=user_id, throw_on_not_found=True)
            user = user[0]

            email_message = MessageResponse(
                message=Message(
                    subject="New Form Response!!",
                    body=EmailBody(
                        contentType="Text",
                        content=f'There is a new form response for "{form_template.name}". Check it out on the Tallulah portal.',
                    ),
                    toRecipients=[ToRecipient(emailAddress=EmailAddress(address=user.email, name=user.name))],
                )
            )
            await client.send_email(email_message)
    except Exception as e:
        log_manager.ERROR({"message": f"Error: while sending email notifications: {e}"})


@router.post(
    path="/",
    description="Add a new form data",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="add_form_data",
)
async def add_form_data(
    background_tasks: BackgroundTasks,
    form_data: RegisterFormData_In = Body(description="Form data information"),
) -> RegisterFormData_Out:

    # Check if the form template exists
    _ = await FormTemplates.read(template_id=form_data.form_template_id, throw_on_not_found=True)

    form_data_db = FormData_Db(
        form_template_id=form_data.form_template_id,
        values=clean_fields(form_data.values),
    )
    await FormDatas.create(form_data_db)

    try:
        # Add the form data to elasticsearch for search
        elastic_client = ElasticsearchClient()
        await elastic_client.insert_document(
            index_name=str(form_data.form_template_id),
            id=str(form_data_db.id),
            document=jsonable_encoder(form_data_db, exclude=set(["_id", "id"])),
        )
    except Exception as e:
        log_manager.ERROR({"message": f"Error while adding form data to elasticsearch: {e}"})
        # raise HTTPException(
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     detail="Error while adding form data to elasticsearch",
        # )

    # Send email notifications
    async_task_manager = AsyncTaskManager()
    async_task_manager.create_task(notify_users(form_data.form_template_id))

    # Generate Tags
    background_tasks.add_task(generate_tags, form_data_db)

    return RegisterFormData_Out(id=form_data_db.id)


@router.post(
    path="/manual",
    description="Add a new form data manually from an authenticated user",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="add_form_data_manual",
)
async def add_form_data_manual(
    background_tasks: BackgroundTasks,
    form_data: RegisterFormData_In = Body(description="Form data information for manual entry"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterFormData_Out:

    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_data.form_template_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    form_data_db = FormData_Db(
        form_template_id=form_data.form_template_id,
        values=form_data.values,
        creation_time=form_data.creation_time if form_data.creation_time else datetime.utcnow(),
    )
    await FormDatas.create(form_data_db)

    # Add the form data to elasticsearch for search
    elastic_client = ElasticsearchClient()
    await elastic_client.insert_document(
        index_name=str(form_data.form_template_id),
        id=str(form_data_db.id),
        document=jsonable_encoder(form_data_db, exclude=set(["_id", "id"])),
    )

    # Generate Tags
    background_tasks.add_task(generate_tags, form_data_db)

    return RegisterFormData_Out(id=form_data_db.id)


@router.put(
    path="/",
    description="Get all the form data for the current user for the template",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_all_form_data",
)
async def get_all_form_data(
    form_template_id: PyObjectId = Query(description="Form template id"),
    skip: int = Query(default=0, description="Number of emails to skip"),
    limit: int = Query(default=200, description="Number of emails to return"),
    sort_key: str = Query(default="creation_time", description="Sort key"),
    sort_direction: int = Query(default=-1, description="Sort direction"),
    filters: FormFilter_In = Body(default=None, description="Filter key"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleFormData_Out:

    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_template_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    form_data_list = await FormDatas.read(
        form_template_id=form_template_id,
        skip=skip,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
        data_filter=filters,
        throw_on_not_found=False,
    )

    form_data_count = await FormDatas.count(form_template_id=form_template_id, data_filter=filters)

    return GetMultipleFormData_Out(
        form_data=[GetFormData_Out(**form_data.dict()) for form_data in form_data_list],
        count=form_data_count,
        next=skip + limit,
        limit=limit,
    )


@router.put(
    path="/{form_data_id}",
    description="Update the form data for the current user",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="update_form_data",
)
async def update_form_data(
    form_data_id: PyObjectId = Path(description="Form data id"),
    form_data: UpdateFormData_In = Body(description="Form data values information to be updated"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:

    current_form_data = await FormDatas.read(form_data_id=form_data_id, throw_on_not_found=True)
    if not current_form_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No form data found for id: {form_data_id}",
        )

    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=current_form_data[0].form_template_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )

    # Update the form data
    await FormDatas.update(
        query_form_data_id=form_data_id, update_form_data_values=form_data.values, throw_on_no_update=False
    )

    # Read the form data again to get the updated values
    updated_form_data = await FormDatas.read(form_data_id=form_data_id, throw_on_not_found=True)
    updated_form_data = updated_form_data[0]

    # Update the form data in elasticsearch for search
    elastic_client = ElasticsearchClient()
    await elastic_client.update_document(
        index_name=str(current_form_data[0].form_template_id),
        id=str(form_data_id),
        document=jsonable_encoder(updated_form_data, exclude=set(["_id", "id"])),
    )

    return Response(status_code=status.HTTP_200_OK)


@router.get(
    path="/upload",
    description="Get the upload url for the form data",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_upload_url",
)
async def get_upload_url(
    media_type: FormMediaTypes = Query(description="Media type"),
) -> GetStorageUrl_Out:
    storage_manager = AzureBlobManager(
        secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "form-" + media_type.value.lower()
    )

    # Get the upload url
    media_id = PyObjectId()
    upload_url = storage_manager.generate_write_sas(str(media_id))

    return GetStorageUrl_Out(id=media_id, url=upload_url)


@router.get(
    path="/download",
    description="Get the download url for the form media",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_download_url",
)
async def get_download_url(
    form_data_id: PyObjectId = Query(description="Form media id"),
    media_type: FormMediaTypes = Query(description="Media type"),
) -> GetStorageUrl_Out:
    # TODO: Check if the user is the owner of the form media data
    # Add media ownership to the database
    storage_manager = AzureBlobManager(
        secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "form-" + media_type.value.lower()
    )

    # Get the download url
    download_url = storage_manager.generate_read_sas(str(form_data_id))

    return GetStorageUrl_Out(id=form_data_id, url=download_url)


@router.get(
    path="/zipcodes",
    description="Get the zipcodes for all the form data for the template",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_zipcodes",
)
async def get_zipcodes(
    form_template_id: PyObjectId = Query(description="Form template id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetFormDataLocation_Out:
    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_template_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    form_data_list = await FormDatas.aggregate_zipcodes(form_template_id=form_template_id)

    return GetFormDataLocation_Out(form_data_location=form_data_list)


@router.get(
    path="/search",
    description="Search the text form data for the current user for the template",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="search_form_data",
)
async def search_form_data(
    form_template_id: PyObjectId = Query(description="Form template id"),
    search_query: str = Query(description="Search query"),
    skip: int = Query(default=0, description="Number of form data to skip"),
    limit: int = Query(default=10, description="Number of form data to return"),
    current_user: TokenData = Depends(get_current_user),
):
    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_template_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    # Search the form data
    elastic_client = ElasticsearchClient()
    response = await elastic_client.search(
        index_name=str(form_template_id), search_query=search_query, skip=skip, size=limit
    )

    return response


@router.get(
    path="/{form_data_id}",
    description="Get the response data for the form",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_form_data",
)
async def get_form_data(
    form_data_id: PyObjectId = Path(description="Form data id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetFormData_Out:
    form_data = await FormDatas.read(form_data_id=form_data_id, throw_on_not_found=True)

    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_data[0].form_template_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    return GetFormData_Out(**form_data[0].dict())


@router.post(
    path="/{form_data_id}/generate-metadata",
    description="Generate metadata for the form data",
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="generate_metadata",
)
async def generate_metadata(
    form_data_id: PyObjectId = Path(description="Form data id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:

    form_data = await FormDatas.read(form_data_id=form_data_id, throw_on_not_found=True)

    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_data[0].form_template_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )

    # if the lock on the form data is acquired, return as the metadata is already being generated
    lock_store = RedisLockStore()
    is_locked = await lock_store.is_locked(f"form_data_{str(form_data_id)}")
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Metadata generation is already in progress. Please try again later after 10 minutes.",
        )

    # Only generate metadata if it has been more than 5 minutes since the last time it was generated
    # else throw a error saying warning about the rate limit
    if form_data[0].metadata:
        time_diff = datetime.utcnow() - form_data[0].metadata.creation_time
        if time_diff.total_seconds() < 300:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again after 5 minutes.",
            )

    log_manager.DEBUG({"message": f"Pushing a message {form_data_id} to the task queue to generate structured data"})
    task_queue = RabbitMQProducerConsumer(
        queue_name=MessageQueueTypes.FORM_DATA_METADATA_GENERATION,
        connection_string=f"{secret_store.RABBIT_MQ_HOST}:5672",
    )
    await task_queue.connect()
    await task_queue.push_message(str(form_data_id))

    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.delete(
    path="/{form_data_id}",
    description="Delete the response template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_form_data",
)
async def delete_form_data(
    form_data_id: PyObjectId = Path(description="Form data id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # TODO: Very bad approach to delete. Improve it. Maybe use aggregation to delete
    form_data = await FormDatas.read(form_data_id=form_data_id, throw_on_not_found=True)

    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_data[0].form_template_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    # Delete the response template
    await FormDatas.update(
        query_form_data_id=form_data_id,
        update_form_data_state=FormDataState.DELETED,
    )

    # Delete from the elastic search cluster as well
    elastic_client = ElasticsearchClient()
    await elastic_client.delete_document(index_name=str(form_data[0].form_template_id), id=str(form_data_id))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    path="/test/backfill_tags",
    description="Backfill the tags",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="backfill_tags",
)
async def backfill_tags(background_tasks: BackgroundTasks):
    # Generate Tags
    background_tasks.add_task(generate_all_tags)
    background_tasks.add_task(generate_all_themes)

    return Response(status_code=status.HTTP_200_OK)


@router.get(
    path="/test/backfill_metadata",
    description="Backfill the metadata",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    dependencies=[Depends(RoleChecker(allowed_roles=[]))],
    operation_id="backfill_metadata",
)
async def backfill_metadata(background_tasks: BackgroundTasks):
    # Generate metadata
    background_tasks.add_task(queue_form_data_metadata_generation)

    return Response(status_code=status.HTTP_200_OK)


@router.get(
    path="/test/generate-all-metadata",
    description="Backfill the metadata",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    dependencies=[Depends(RoleChecker(allowed_roles=[]))],
    operation_id="generate_all_metadata",
)
async def generate_all_metadata(background_tasks: BackgroundTasks):
    # Generate metadata
    background_tasks.add_task(queue_all_form_data_metadata_generation)

    return Response(status_code=status.HTTP_200_OK)


async def generate_tags(form_data: FormData_Db):
    await generate_tag_for_form(form_data=form_data)
    await generate_theme_for_story(form_data=form_data)


async def generate_tag_for_form(form_data: FormData_Db):
    logger.info(f"Generating tags for form data: {form_data.id}")
    # preferred_tags = ""
    patient = FormDatas.convert_form_data_to_string(form_data)
    # Get the tags
    messages = [
        {
            "role": "system",
            "content": """
        You are an assistant who helps with reading patient data and providing tags for the data.
        Don't forget to separate the tags with commas and no special characters. Do not include personal information.
    """,
        }
    ]
    # messages.append({"role": "user", "content": "Pick from the following tags, if possible, and don't hesitate to add new ones: " + preferred_tags})
    messages.append({"role": "user", "content": patient})
    openai = OpenAiGenerator(secret_store.OPENAI_API_BASE, secret_store.OPENAI_API_KEY)
    generated_content = await openai.get_response(messages=messages)
    if generated_content is None:
        logger.error(f"OpenAI Could not generate tags: {form_data.id}")
        return
    logger.info(f"Generated: {form_data.id} {generated_content}")
    tags = generated_content.split(",")
    tags = [tag.strip() for tag in tags]
    tags = list(set(tags))

    await FormDatas.update(query_form_data_id=form_data.id, update_form_data_tags=tags, throw_on_no_update=False)


async def generate_theme_for_story(form_data: FormData_Db):
    logger.info(f"Generating themes for form data: {form_data.id}")
    if "patientStory" not in form_data.values:
        logger.error(f"No patient story found in form data: {form_data.id}")
        return
    patient_story = form_data.values["patientStory"]["value"]
    if not patient_story:
        return

    messages = [
        {
            "role": "system",
            "content": """
        You are an assistant who helps with reading patient stories and providing themes for those stories. Provide at most 5 themes.
        Don't forget to separate the themes with commas and no special characters. Do not include personal information.
    """,
        }
    ]
    messages.append({"role": "user", "content": patient_story})
    openai = OpenAiGenerator(secret_store.OPENAI_API_BASE, secret_store.OPENAI_API_KEY)
    generated_content = await openai.get_response(messages=messages)
    if generated_content is None:
        logger.error(f"OpenAI Could not generate themes: {form_data.id}")
        return
    # TODO: Check if generated_content is not 'Sorry', 'Apologies', etc.
    logger.info(f"Generated: {form_data.id} {generated_content}")
    themes = generated_content.split(",")
    themes = [theme.strip() for theme in themes]
    themes = list(set(themes))
    await FormDatas.update(query_form_data_id=form_data.id, update_form_data_themes=themes, throw_on_no_update=False)


async def generate_all_tags():
    # Get all the form data
    form_data = await FormDatas.read_forms_without_tags()
    if not form_data:
        return

    # Process one at a time
    for data in form_data:
        try:
            await generate_tag_for_form(data)
            await asyncio.sleep(2)
        except Exception as e:
            print(e)
            logger.error(f"Error generating tags for form data: {data.id}")


async def generate_all_themes():
    # Get all the form data
    form_data = await FormDatas.read(field_not_exists="themes", throw_on_not_found=False)
    if not form_data:
        return

    # Process one at a time
    for data in form_data:
        try:
            await generate_theme_for_story(data)
            await asyncio.sleep(2)
        except Exception as e:
            print(e)
            logger.error(f"Error generating themes for form data: {data.id}")


@router.get(
    path="/deduplicate/{form_template_id}",
    description="Deduplicate form data for a given form template",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="deduplicate_form_data",
)
async def deduplicate_form_data(
    form_template_id: PyObjectId = Path(description="Form template id"),
    current_user: TokenData = Depends(get_current_user),
):
    organization_id = current_user.organization_id
    organization_id = "bf863520-5dea-4447-9e3e-b85044c323ed"
    # form_template_id = "eec41736-f197-4d8b-8373-47ff7207237c"

    # Get all the form data for the template
    form_data_list = await FormDatas.read(
        form_template_id=form_template_id,
        throw_on_not_found=False,
    )
    if not form_data_list:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    original_forms = []
    duplicate_forms = []

    for form_data in form_data_list:
        # Check if the form data is already processed
        if form_data.metadata and form_data.state == FormDataState.DELETED:
            continue
        
        is_duplicate = False
        for form in original_forms:
            if form_data.values == form.values or (form.values.get("Your name") and form.values.get("Zip Code") and form.values.get("Your name") == form_data.values.get("Your name") and form.values.get("Zip Code") == form_data.values.get("Zip Code")):
                duplicate_forms.append(form_data)
                is_duplicate = True
                print(f"Duplicate found: {form_data.id} is a duplicate of {form.id}")
                break
        if not is_duplicate:
            original_forms.append(form_data)

    print(f"Original forms: {len(original_forms)}, Duplicate forms: {len(duplicate_forms)}")

    for form_data in duplicate_forms:
        # Delete the duplicate form data
        await FormDatas.update(
            query_form_data_id=form_data.id,
            update_form_data_state=FormDataState.DELETED,
            throw_on_no_update=False,
        )
        print(f"Deleted form data: {form_data.id}")
        # Delete from elasticsearch
        elastic_client = ElasticsearchClient()
        try:
            await elastic_client.delete_document(
                index_name=str(form_template_id), id=str(form_data.id)
            )
        except Exception as e:
            logger.error(f"Error deleting form data from elasticsearch: {e}")

    return Response(
        status_code=status.HTTP_200_OK,
    )


@router.get(
    path="/reindex/{form_template_id}",
    description="Reindex form data in ES",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="reindex_form_data",
)
async def reindex_form_data(
    form_template_id: PyObjectId = Path(description="Form template id"),
    current_user: TokenData = Depends(get_current_user),
):
    organization_id = current_user.organization_id
    # form_template_id = "eec41736-f197-4d8b-8373-47ff7207237c"

    # Get all the form data for the template
    form_data_list = await FormDatas.read(
        form_template_id=form_template_id,
        throw_on_not_found=False,
    )
    if not form_data_list:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    elastic_client = ElasticsearchClient()
    for form_data in form_data_list:
        try:
            # get the form data from elasticsearch
            existing_document = await elastic_client.get_document(
                index_name=str(form_template_id),
                id=str(form_data.id),
            )
            if existing_document:
                if form_data.state == FormDataState.DELETED:
                    # If the form data is deleted, delete it from elasticsearch
                    await elastic_client.delete_document(
                        index_name=str(form_template_id),
                        id=str(form_data.id),
                    )
                    logger.info(f"Deleted form data from elasticsearch: {form_data.id}")
                    continue
                continue
            if form_data.state == FormDataState.DELETED:
                continue
            # Clean the fields before reindexing
            form_data.values = clean_fields(form_data.values)
            await elastic_client.insert_document(
                index_name=str(form_template_id),
                id=str(form_data.id),
                document=jsonable_encoder(form_data, exclude=set(["_id", "id"])),
            )
        except Exception as e:
            logger.error(f"Error reindexing form data: {e}")

    return Response(status_code=status.HTTP_200_OK)