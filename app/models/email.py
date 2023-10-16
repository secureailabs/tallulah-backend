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
    UNPROCESSED = "UNPROCESSED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class Email_Base(SailBaseModel):
    subject: Optional[StrictStr] = Field(default=None)
    body: Optional[Dict] = Field(default_factory=dict)
    from_address: Dict = Field()
    received_time: str = Field()
    mailbox_id: PyObjectId = Field()
    note: Optional[StrictStr] = Field(default=None)
    tags: List[StrictStr] = Field(default=[])
    message_state: EmailState = Field(default=EmailState.UNPROCESSED)


class Email_Db(Email_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetEmail_Out(Email_Base):
    id: PyObjectId = Field(alias="_id")
    creation_time: datetime = Field()


class GetMultipleEmail_Out(SailBaseModel):
    messages: List[GetEmail_Out] = Field()
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
        email_id: Optional[PyObjectId] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        throw_on_not_found: bool = True,
    ) -> List[Email_Db]:
        messages_list = []

        query = {}
        if email_id:
            query["_id"] = str(email_id)
        if mailbox_id:
            query["mailbox_id"] = str(mailbox_id)

        if skip is None and limit is None:
            response = await Emails.data_service.find_by_query(
                collection=Emails.DB_COLLECTION_EMAILS,
                query=jsonable_encoder(query),
            )
        elif skip is not None and limit is not None:
            response = await Emails.data_service.find_sorted_pagination(
                collection=Emails.DB_COLLECTION_EMAILS,
                query=jsonable_encoder(query),
                sort_key="received_time",
                sort_direction=-1,
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
    ):
        query = {}
        if query_message_id:
            query["_id"] = str(query_message_id)

        update_request = {"$set": {}}
        if update_message_state:
            update_request["$set"]["message_state"] = update_message_state.value

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
