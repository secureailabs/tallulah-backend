# -------------------------------------------------------------------------------
# Engineering
# accounts.py
# -------------------------------------------------------------------------------
"""Models used by account management service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Secure Ai Labs, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Secure Ai Labs, Inc.
# -------------------------------------------------------------------------------

import mailbox
from datetime import datetime
from enum import Enum
from typing import List, Optional

from click import UNPROCESSED
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, Field, StrictStr

from app.data import operations as data_service
from app.models.common import BasicObjectInfo, PyObjectId, SailBaseModel


class MessageType(Enum):
    EMAIL = "EMAIL"
    REDDIT = "REDDIT"
    YOUTUBE_TRANSCRIPT = "YOUTUBE_TRANSCRIPT"


class MessageState(Enum):
    UNPROCESSED = "UNPROCESSED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class Message_Base(SailBaseModel):
    source: str = Field()
    message: StrictStr = Field()
    message_type: MessageType = Field()
    note: Optional[StrictStr] = Field(default=None)
    message_state: MessageState = Field(default=MessageState.UNPROCESSED)


class Message_Db(Message_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetMessage_Out(Message_Base):
    id: PyObjectId = Field(alias="_id")
    creation_time: datetime = Field()


class UpdateMessage_In(SailBaseModel):
    message_state: MessageState = Field()


class Messages:
    DB_COLLECTION_USERS = "messages"

    @staticmethod
    async def create(
        message: Message_Db,
    ):
        return await data_service.insert_one(
            collection=Messages.DB_COLLECTION_USERS,
            data=jsonable_encoder(message),
        )

    @staticmethod
    async def read(
        job_id: Optional[PyObjectId] = None,
        message_id: Optional[PyObjectId] = None,
        throw_on_not_found: bool = True,
    ) -> List[Message_Db]:
        messages_list = []

        query = {}
        if message_id:
            query["_id"] = str(message_id)
        if job_id:
            query["job_id"] = str(job_id)

        response = await data_service.find_by_query(
            collection=Messages.DB_COLLECTION_USERS,
            query=jsonable_encoder(query),
        )

        if response:
            for data_model in response:
                messages_list.append(Message_Db(**data_model))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No messages found for query: {query}",
            )

        return messages_list

    @staticmethod
    async def update(
        query_message_id: Optional[PyObjectId] = None,
        update_message_state: Optional[MessageState] = None,
    ):
        query = {}
        if query_message_id:
            query["_id"] = str(query_message_id)

        update_request = {"$set": {}}
        if update_message_state:
            update_request["$set"]["message_state"] = update_message_state.value

        update_response = await data_service.update_many(
            collection=Messages.DB_COLLECTION_USERS,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message not found or no changes to update",
            )
