# -------------------------------------------------------------------------------
# Engineering
# response_templates.py
# -------------------------------------------------------------------------------
"""Models used by response template management service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel
from app.utils.emails import EmailBody


class ResponseTemplate_Base(SailBaseModel):
    name: StrictStr = Field()
    subject: Optional[StrictStr] = Field(default=None)
    body: Optional[EmailBody] = Field(default=None)
    note: Optional[StrictStr] = Field(default=None)


class RegisterResponseTemplate_In(ResponseTemplate_Base):
    pass


class RegisterResponseTemplate_Out(SailBaseModel):
    id: PyObjectId = Field(alias="_id")


class ResponseTemplate_Db(ResponseTemplate_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    last_edit_time: datetime = Field(default_factory=datetime.utcnow)


class GetResponseTemplate_Out(ResponseTemplate_Base):
    id: PyObjectId = Field(alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    last_edit_time: datetime = Field(default_factory=datetime.utcnow)


class GetMultipleResponseTemplate_Out(SailBaseModel):
    templates: List[GetResponseTemplate_Out] = Field()


class UpdateResponseTemplate_In(SailBaseModel):
    subject: Optional[StrictStr] = Field(default=None)
    body: Optional[EmailBody] = Field(default=None)
    note: Optional[StrictStr] = Field(default=None)


class ResponseTemplates:
    DB_COLLECTION_RESPONSE_TEMPLATES = "response_templates"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        response_template: ResponseTemplate_Db,
    ):
        return await ResponseTemplates.data_service.insert_one(
            collection=ResponseTemplates.DB_COLLECTION_RESPONSE_TEMPLATES,
            data=jsonable_encoder(response_template),
        )

    @staticmethod
    async def read(
        user_id: Optional[PyObjectId] = None,
        template_id: Optional[PyObjectId] = None,
        throw_on_not_found: bool = True,
    ) -> List[ResponseTemplate_Db]:
        response_template_list = []

        query = {}
        if template_id:
            query["_id"] = str(template_id)
        if user_id:
            query["user_id"] = str(user_id)

        response = await ResponseTemplates.data_service.find_by_query(
            collection=ResponseTemplates.DB_COLLECTION_RESPONSE_TEMPLATES,
            query=jsonable_encoder(query),
        )

        if response:
            for response_template in response:
                response_template_list.append(ResponseTemplate_Db(**response_template))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No messages found for query: {query}",
            )

        return response_template_list

    @staticmethod
    async def update(
        query_response_template_id: Optional[PyObjectId] = None,
        query_user_id: Optional[PyObjectId] = None,
        update_response_template_subject: Optional[StrictStr] = None,
        update_response_template_body: Optional[EmailBody] = None,
        update_response_template_note: Optional[StrictStr] = None,
        update_response_template_last_edit_time: Optional[datetime] = None,
    ):
        query = {}
        if query_response_template_id:
            query["_id"] = str(query_response_template_id)
        if query_user_id:
            query["user_id"] = str(query_user_id)

        update_request = {"$set": {}}
        if update_response_template_subject:
            update_request["$set"]["subject"] = update_response_template_subject
        if update_response_template_body:
            update_request["$set"]["body"] = update_response_template_body
        if update_response_template_note:
            update_request["$set"]["note"] = update_response_template_note
        if update_response_template_last_edit_time:
            update_request["$set"]["last_edit_time"] = update_response_template_last_edit_time

        update_response = await ResponseTemplates.data_service.update_many(
            collection=ResponseTemplates.DB_COLLECTION_RESPONSE_TEMPLATES,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ResponseTemplate not found or no changes to update",
            )

    @staticmethod
    async def delete(
        query_response_template_id: Optional[PyObjectId] = None,
        query_user_id: Optional[PyObjectId] = None,
    ):
        query = {}
        if query_response_template_id:
            query["_id"] = str(query_response_template_id)
        if query_user_id:
            query["user_id"] = str(query_user_id)

        delete_response = await ResponseTemplates.data_service.delete(
            collection=ResponseTemplates.DB_COLLECTION_RESPONSE_TEMPLATES,
            query=query,
        )

        if delete_response.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ResponseTemplate not found or no changes to delete",
            )
