# -------------------------------------------------------------------------------
# Engineering
# content_generation.py
# -------------------------------------------------------------------------------
"""Models used by content generation service"""
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
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class ContentGenerationState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class ContentGeneration_Base(SailBaseModel):
    template_id: PyObjectId = Field()
    values: Dict = Field()


class ContentGeneration_Db(ContentGeneration_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[PyObjectId] = Field(default=None)
    organization_id: PyObjectId = Field()
    generated: Optional[StrictStr] = Field(default=None)
    state: ContentGenerationState = Field(default=ContentGenerationState.ACTIVE)
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetContentGeneration_Out(ContentGeneration_Base):
    id: PyObjectId = Field()
    state: ContentGenerationState = Field()
    generated: Optional[StrictStr] = Field(default=None)
    creation_time: datetime = Field()


class GetMultipleContentGeneration_Out(SailBaseModel):
    content_generations: List[GetContentGeneration_Out]
    count: int
    limit: int
    next: int


class RegisterContentGeneration_In(ContentGeneration_Base):
    pass


class RegisterContentGeneration_Out(SailBaseModel):
    id: PyObjectId = Field()
    generated: StrictStr = Field()


class ContentGenerations:
    DB_COLLECTION_CONTENT_GENERATION = "content-generation"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        content_generation: ContentGeneration_Db,
    ):
        return await ContentGenerations.data_service.insert_one(
            collection=ContentGenerations.DB_COLLECTION_CONTENT_GENERATION,
            data=jsonable_encoder(content_generation),
        )

    @staticmethod
    async def read(
        user_id: Optional[PyObjectId] = None,
        organization_id: Optional[PyObjectId] = None,
        content_generation_id: Optional[PyObjectId] = None,
        content_generation_state: Optional[ContentGenerationState] = None,
        content_generation_template_id: Optional[PyObjectId] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_key: str = "creation_time",
        sort_direction: int = -1,
        throw_on_not_found: bool = True,
    ) -> List[ContentGeneration_Db]:
        conversations_list = []
        query = {}
        if content_generation_id:
            query["_id"] = str(content_generation_id)
        if content_generation_template_id:
            query["template_id"] = str(content_generation_template_id)
        if user_id:
            query["user_id"] = str(user_id)
        if organization_id:
            query["organization_id"] = str(organization_id)
        if content_generation_state:
            query["state"] = content_generation_state

        if skip is None and limit is None:
            response = await ContentGenerations.data_service.find_by_query(
                collection=ContentGenerations.DB_COLLECTION_CONTENT_GENERATION,
                query=jsonable_encoder(query),
            )
        elif skip is not None and limit is not None:
            response = await ContentGenerations.data_service.find_sorted_pagination(
                collection=ContentGenerations.DB_COLLECTION_CONTENT_GENERATION,
                query=jsonable_encoder(query),
                skip=skip,
                limit=limit,
                sort_key=sort_key,
                sort_direction=sort_direction,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both skip and limit must be provided",
            )

        if response:
            for conversation in response:
                conversations_list.append(ContentGeneration_Db(**conversation))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No conversations found for query: {query}",
            )

        return conversations_list

    @staticmethod
    async def update(
        query_content_generation_id: Optional[PyObjectId] = None,
        update_generated_content: Optional[StrictStr] = None,
        update_state: Optional[ContentGenerationState] = None,
        update_error_message: Optional[StrictStr] = None,
    ):
        query = {}
        if query_content_generation_id:
            query["_id"] = str(query_content_generation_id)

        update_request = {"$set": {}}
        if update_state:
            update_request["$set"]["state"] = update_state
        if update_error_message:
            update_request["$set"]["error_message"] = update_error_message
        if update_generated_content:
            update_request["$set"]["generated"] = update_generated_content

        update_response = await ContentGenerations.data_service.update_many(
            collection=ContentGenerations.DB_COLLECTION_CONTENT_GENERATION,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation not found or no changes to update",
            )

    @staticmethod
    async def count(
        content_generation_template_id: Optional[PyObjectId] = None,
    ) -> int:
        query = {}
        if content_generation_template_id:
            query["template_id"] = str(content_generation_template_id)

        return await ContentGenerations.data_service.sail_db[
            ContentGenerations.DB_COLLECTION_CONTENT_GENERATION
        ].count_documents(query)
