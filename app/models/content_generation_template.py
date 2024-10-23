# -------------------------------------------------------------------------------
# Engineering
# content_generation_template.py
# -------------------------------------------------------------------------------
"""Models used by content generation template service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
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
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class ParametersType(Enum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    TIME = "TIME"
    DATETIME = "DATETIME"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    URL = "URL"
    TEXTAREA = "TEXTAREA"
    SELECT = "SELECT"
    RADIO = "RADIO"
    CHECKBOX = "CHECKBOX"


class ParameterField(SailBaseModel):
    name: StrictStr = Field()
    label: StrictStr = Field()
    description: Optional[StrictStr] = Field(default=None)
    place_holder: StrictStr = Field(default=None)
    type: ParametersType = Field(default=ParametersType.TEXT)
    required: bool = Field(default=False)
    options: List[StrictStr] = Field(default=None)


class Context(SailBaseModel):
    role: StrictStr = Field()
    content: StrictStr = Field()


class ContentGenerationState(Enum):
    TEMPLATE = "TEMPLATE"
    PUBLISHED = "PUBLISHED"
    DELETED = "DELETED"


class ContentGenerationTemplate_Base(SailBaseModel):
    name: StrictStr = Field()
    description: Optional[StrictStr] = Field(default=None)
    parameters: List[ParameterField] = Field(default=None)
    context: List[Context] = Field(default=None)
    prompt: StrictStr = Field()
    is_public: bool = Field(default=False)


class ContentGenerationTemplate_Db(ContentGenerationTemplate_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    state: ContentGenerationState = Field(default=ContentGenerationState.TEMPLATE)


class GetContentGenerationTemplate_Out(ContentGenerationTemplate_Base):
    id: PyObjectId = Field()
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    creation_time: datetime = Field()
    state: ContentGenerationState = Field()


class GetMultipleContentGenerationTemplate_Out(SailBaseModel):
    templates: List[GetContentGenerationTemplate_Out] = Field()


class RegisterContentGenerationTemplate_In(ContentGenerationTemplate_Base):
    pass


class RegisterContentGenerationTemplate_Out(SailBaseModel):
    id: PyObjectId = Field()


class UpdateContentGenerationTemplate_In(SailBaseModel):
    name: Optional[StrictStr] = Field(default=None)
    description: Optional[StrictStr] = Field(default=None)
    parameters: Optional[List[ParameterField]] = Field(default=None)
    context: Optional[List[Context]] = Field(default=None)
    prompt: Optional[StrictStr] = Field(default=None)
    is_public: Optional[bool] = Field(default=None)


class ContentGenerationTemplates:
    DB_COLLECTION_CONTENT_GENERATION_TEMPLATE = "content-generation-template"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        content_generation_template: ContentGenerationTemplate_Db,
    ):
        return await ContentGenerationTemplates.data_service.insert_one(
            collection=ContentGenerationTemplates.DB_COLLECTION_CONTENT_GENERATION_TEMPLATE,
            data=jsonable_encoder(content_generation_template),
        )

    @staticmethod
    async def read(
        content_generation_template_id: Optional[PyObjectId] = None,
        organization_id: Optional[PyObjectId] = None,
        state: Optional[ContentGenerationState] = None,
        is_public: Optional[bool] = None,
        throw_on_not_found: bool = True,
    ) -> List[ContentGenerationTemplate_Db]:
        content_generation_template_list = []

        query = {}
        if content_generation_template_id:
            query["_id"] = str(content_generation_template_id)
        if organization_id:
            query["organization_id"] = str(organization_id)
        if is_public:
            query["is_public"] = is_public
        if state:
            query["state"] = state.value
        else:
            query["state"] = {"$ne": ContentGenerationState.DELETED.value}

        response = await ContentGenerationTemplates.data_service.find_by_query(
            collection=ContentGenerationTemplates.DB_COLLECTION_CONTENT_GENERATION_TEMPLATE,
            query=jsonable_encoder(query),
        )

        if response:
            for content_generation_template in response:
                content_generation_template_list.append(ContentGenerationTemplate_Db(**content_generation_template))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No content generation templates found for query: {query}",
            )

        return content_generation_template_list

    @staticmethod
    async def update(
        query_content_generation_template_id: Optional[PyObjectId] = None,
        query_organization_id: Optional[PyObjectId] = None,
        update_content_generation_template_name: Optional[StrictStr] = None,
        update_content_generation_template_state: Optional[ContentGenerationState] = None,
        update_content_generation_template_description: Optional[StrictStr] = None,
        update_content_generation_template_parameters: Optional[List[ParameterField]] = None,
        update_content_generation_template_context: Optional[List[Context]] = None,
        update_content_generation_template_prompt: Optional[StrictStr] = None,
        update_content_generation_template_is_public: Optional[bool] = None,
    ):
        query = {}
        if query_content_generation_template_id:
            query["_id"] = str(query_content_generation_template_id)
        if query_organization_id:
            query["organization_id"] = str(query_organization_id)

        update_request = {"$set": {}}
        if update_content_generation_template_name:
            update_request["$set"]["name"] = update_content_generation_template_name
        if update_content_generation_template_state:
            update_request["$set"]["state"] = update_content_generation_template_state.value
        if update_content_generation_template_description:
            update_request["$set"]["description"] = update_content_generation_template_description
        if update_content_generation_template_parameters:
            update_request["$set"]["parameters"] = update_content_generation_template_parameters
        if update_content_generation_template_context:
            update_request["$set"]["context"] = update_content_generation_template_context
        if update_content_generation_template_prompt:
            update_request["$set"]["prompt"] = update_content_generation_template_prompt
        if update_content_generation_template_is_public:
            update_request["$set"]["is_public"] = update_content_generation_template_is_public

        update_response = await ContentGenerationTemplates.data_service.update_many(
            collection=ContentGenerationTemplates.DB_COLLECTION_CONTENT_GENERATION_TEMPLATE,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No content generation templates found for query: {query}",
            )
