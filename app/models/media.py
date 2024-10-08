# -------------------------------------------------------------------------------
# Engineering
# form_templates.py
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
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models import organizations
from app.models.common import PyObjectId, SailBaseModel


class MediaState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class MediaMetadata_Db(SailBaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    state: MediaState = Field(default=MediaState.ACTIVE)
    organization_id: PyObjectId = Field()
    creation_time: datetime = Field(default=datetime.utcnow())


class MediaMetadata:
    DB_COLLECTION_MEDIA_METADATA = "media-metadata"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        metadata: MediaMetadata_Db,
    ):
        return await MediaMetadata.data_service.insert_one(
            collection=MediaMetadata.DB_COLLECTION_MEDIA_METADATA,
            data=jsonable_encoder(metadata),
        )

    @staticmethod
    async def read(
        media_id: Optional[PyObjectId] = None,
        organization_id: Optional[PyObjectId] = None,
        throw_on_not_found: bool = True,
    ) -> List[MediaMetadata_Db]:
        media_list = []

        query = {}
        if media_id:
            query["_id"] = str(media_id)
        if organization_id:
            query["organization_id"] = str(organization_id)

        # only read the non deleted ones
        query["state"] = MediaState.ACTIVE.value

        response = await MediaMetadata.data_service.find_by_query(
            collection=MediaMetadata.DB_COLLECTION_MEDIA_METADATA,
            query=jsonable_encoder(query),
        )

        if response:
            for media in response:
                media_list.append(MediaMetadata_Db(**media))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No media found for query: {query}",
            )

        return media_list

    @staticmethod
    async def update(
        query_media_metadata_id: PyObjectId,
        update_media_metadata_state: Optional[MediaState] = None,
        throw_on_no_update: bool = True,
    ):
        query = {}
        if query_media_metadata_id:
            query["_id"] = str(query_media_metadata_id)

        update_request = {"$set": {}}
        if update_media_metadata_state:
            update_request["$set"]["state"] = update_media_metadata_state.value

        update_response = await MediaMetadata.data_service.update_one(
            collection=MediaMetadata.DB_COLLECTION_MEDIA_METADATA,
            query=query,
            data=jsonable_encoder(update_request),
        )
        if update_response.modified_count == 0:
            if throw_on_no_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Media not found or no changes to update",
                )
