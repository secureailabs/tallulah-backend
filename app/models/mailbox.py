# -------------------------------------------------------------------------------
# Engineering
# mailboxes.py
# -------------------------------------------------------------------------------
"""Mailboxes used to fetch user emails"""
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
from typing import List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, Field, StrictStr

from app.data import operations as data_service
from app.models.common import PyObjectId, SailBaseModel


class MailboxState(Enum):
    UNPROCESSED = "UNPROCESSED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class MailboxProvider(Enum):
    OUTLOOK = "OUTLOOK"
    GMAIL = "GMAIL"


class Mailbox_Base(SailBaseModel):
    email: EmailStr = Field()
    note: Optional[StrictStr] = Field(default=None)
    user_id: PyObjectId = Field()


class Mailbox_Db(Mailbox_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    refresh_token: StrictStr = Field(default=None)
    last_refresh_time: Optional[str] = Field(default_factory=None)


class GetMailbox_Out(Mailbox_Base):
    id: PyObjectId = Field(alias="_id")
    creation_time: datetime = Field()


class RegisterMailbox_In(SailBaseModel):
    code: str = Field()
    provider: MailboxProvider = Field()


class RegisterMailbox_Out(SailBaseModel):
    id: PyObjectId = Field(alias="_id")


class GetMultipleMailboxes_Out(SailBaseModel):
    mailboxes: List[GetMailbox_Out] = Field()


class Mailboxes:
    DB_COLLECTION_MAILBOXES = "mailboxes"

    @staticmethod
    async def create(
        mailbox: Mailbox_Db,
    ):
        return await data_service.insert_one(
            collection=Mailboxes.DB_COLLECTION_MAILBOXES,
            data=jsonable_encoder(mailbox),
        )

    @staticmethod
    async def read(
        mailbox_id: Optional[PyObjectId] = None,
        user_id: Optional[PyObjectId] = None,
        throw_on_not_found: bool = True,
    ) -> List[Mailbox_Db]:
        mailboxes_list = []

        query = {}
        if mailbox_id:
            query["_id"] = str(mailbox_id)
        if user_id:
            query["user_id"] = str(user_id)

        response = await data_service.find_by_query(
            collection=Mailboxes.DB_COLLECTION_MAILBOXES,
            query=jsonable_encoder(query),
        )

        if response:
            for data_model in response:
                mailboxes_list.append(Mailbox_Db(**data_model))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No mailboxes found for query: {query}",
            )

        return mailboxes_list

    @staticmethod
    async def update(
        query_mailbox_id: Optional[PyObjectId] = None,
        update_last_refresh_time: Optional[str] = None,
        update_refresh_token: Optional[str] = None,
        update_mailbox_state: Optional[MailboxState] = None,
    ):
        query = {}
        if query_mailbox_id:
            query["_id"] = str(query_mailbox_id)

        update = {}
        if update_last_refresh_time:
            update["last_refresh_time"] = update_last_refresh_time
        if update_refresh_token:
            update["refresh_token"] = update_refresh_token
        if update_mailbox_state:
            update["mailbox_state"] = update_mailbox_state

        update_result = await data_service.update_one(
            collection=Mailboxes.DB_COLLECTION_MAILBOXES,
            query=jsonable_encoder(query),
            data=jsonable_encoder({"$set": update}),
        )

        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mailbox not found for query: {query}",
            )
