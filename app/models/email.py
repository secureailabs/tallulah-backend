# -------------------------------------------------------------------------------
# Engineering
# accounts.py
# -------------------------------------------------------------------------------
"""Models used by account management service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class EmailState(Enum):
    NEW = "NEW"
    TAGGED = "TAGGED"
    RESPONDED = "RESPONDED"
    FAILED = "FAILED"


class Annotation(SailBaseModel):
    annotation_id: PyObjectId = Field(default_factory=PyObjectId)
    source: StrictStr = Field()
    label: StrictStr = Field()
    label_scores: Dict[str, float] = Field()


class Email_Base(SailBaseModel):
    subject: Optional[StrictStr] = Field(default=None)
    body: Optional[Dict] = Field(default_factory=dict)
    from_address: Dict = Field()
    received_time: str = Field()
    mailbox_id: PyObjectId = Field()
    user_id: PyObjectId = Field()
    annotations: List[Annotation] = Field(default=[])
    note: Optional[StrictStr] = Field(default=None)
    message_state: EmailState = Field(default=EmailState.NEW)
    outlook_id: StrictStr = Field()


class Email_Db(Email_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetEmail_Out(Email_Base):
    id: PyObjectId = Field(alias="_id")
    creation_time: datetime = Field()


class GetMultipleEmail_Out(SailBaseModel):
    messages: List[GetEmail_Out] = Field()
    count: int = Field()
    next: int = Field()
    limit: int = Field()


class UpdateEmail_In(SailBaseModel):
    message_state: EmailState = Field()


class Emails:
    DB_COLLECTION_EMAILS = "emails"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        email: Email_Db,
    ):
        return await Emails.data_service.insert_one(
            collection=Emails.DB_COLLECTION_EMAILS,
            data=jsonable_encoder(email),
        )

    @staticmethod
    async def read(
        mailbox_id: Optional[PyObjectId] = None,
        user_id: Optional[PyObjectId] = None,
        email_id: Optional[PyObjectId] = None,
        filter_tags: Optional[List[str]] = None,
        filter_state: Optional[List[EmailState]] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_key: str = "received_time",
        sort_direction: int = -1,
        throw_on_not_found: bool = True,
    ) -> List[Email_Db]:
        messages_list = []
        # TODO: Use a builder pattern or an ODM to build the query
        query = {}
        if email_id:
            query["_id"] = str(email_id)
        if user_id:
            query["user_id"] = str(user_id)
        if mailbox_id:
            query["mailbox_id"] = str(mailbox_id)
        if filter_tags:
            query["annotations.label"] = {"$in": filter_tags}
        if filter_state:
            query["message_state"] = {"$in": [state.value for state in filter_state]}

        if skip is None and limit is None:
            response = await Emails.data_service.find_by_query(
                collection=Emails.DB_COLLECTION_EMAILS,
                query=jsonable_encoder(query),
            )
        elif skip is not None and limit is not None:
            response = await Emails.data_service.find_sorted_pagination(
                collection=Emails.DB_COLLECTION_EMAILS,
                query=jsonable_encoder(query),
                sort_key=sort_key,
                sort_direction=sort_direction,
                skip=skip,
                limit=limit,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid skip and limit values: {skip} and {limit}",
            )

        if response:
            for data_model in response:
                messages_list.append(Email_Db(**data_model))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No messages found for query: {query}",
            )

        return messages_list

    @staticmethod
    async def update(
        query_message_id: Optional[PyObjectId] = None,
        update_message_state: Optional[EmailState] = None,
        update_message_note: Optional[StrictStr] = None,
    ):
        query = {}
        if query_message_id:
            query["_id"] = str(query_message_id)

        update_request = {"$set": {}}
        if update_message_state:
            update_request["$set"]["message_state"] = update_message_state.value
        if update_message_note:
            update_request["$set"]["note"] = update_message_note

        update_response = await Emails.data_service.update_many(
            collection=Emails.DB_COLLECTION_EMAILS,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email not found or no changes to update",
            )

    @staticmethod
    async def count(
        mailbox_id: Optional[PyObjectId] = None,
        filter_tags: Optional[List[str]] = None,
    ) -> int:
        query = {}
        if mailbox_id:
            query["mailbox_id"] = str(mailbox_id)
        if filter_tags:
            query["annotations.label"] = {"$in": filter_tags}

        return await Emails.data_service.sail_db[Emails.DB_COLLECTION_EMAILS].count_documents(query)

    @staticmethod
    async def delete(
        query_message_id: Optional[PyObjectId] = None,
        mailbox_id: Optional[PyObjectId] = None,
    ):
        query = {}
        if query_message_id:
            query["_id"] = str(query_message_id)
        if mailbox_id:
            query["mailbox_id"] = str(mailbox_id)

        delete_response = await Emails.data_service.delete(
            collection=Emails.DB_COLLECTION_EMAILS,
            query=query,
        )

        if delete_response.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email not found or no changes to update",
            )
