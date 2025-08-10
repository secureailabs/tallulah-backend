# -------------------------------------------------------------------------------
# Engineering
# etapestry_data.py
# -------------------------------------------------------------------------------
"""Models used by eTapestry data management service"""
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
from pydantic import Field

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel
from app.utils.etapestry import AccountInfo


class ETapestryDataState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class ETapestryData_Base(SailBaseModel):
    repository_id: PyObjectId = Field()
    account: AccountInfo = Field()
    state: ETapestryDataState = Field(default=ETapestryDataState.ACTIVE)
    notes: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    photos: Optional[List[PyObjectId]] = Field(default=None)
    videos: Optional[List[PyObjectId]] = Field(default=None)


class ETapestryData_Db(ETapestryData_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class UpdateETapestryData_In(SailBaseModel):
    state: Optional[ETapestryDataState] = Field(default=None)  # TODO: Prawal dont allow this
    notes: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    photos: Optional[List[PyObjectId]] = Field(default=None)
    videos: Optional[List[PyObjectId]] = Field(default=None)


class GetETapestryData_Out(ETapestryData_Base):
    id: PyObjectId = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetMultipleETapestryData_Out(SailBaseModel):
    etapestry_data: List[GetETapestryData_Out] = Field()
    count: int = Field()
    next: int = Field()
    limit: int = Field()


class ETapestryDatas:
    DB_COLLECTION_ETAPESTRY_DATA = "etapestry-data"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        etapestry_data: ETapestryData_Db,
    ) -> ETapestryData_Db:
        # check if the account exists
        query_request = {}
        query_request["repository_id"] = str(etapestry_data.repository_id)
        query_request["account.id"] = etapestry_data.account.id

        account = await ETapestryDatas.data_service.find_one(
            collection=ETapestryDatas.DB_COLLECTION_ETAPESTRY_DATA,
            query=jsonable_encoder(query_request),
        )
        if not account:
            await ETapestryDatas.data_service.insert_one(
                collection=ETapestryDatas.DB_COLLECTION_ETAPESTRY_DATA,
                data=jsonable_encoder(etapestry_data),
            )
        else:
            # Use the same id
            etapestry_data.id = account["_id"]
            if "notes" in account:
                etapestry_data.notes = account["notes"]
            if "tags" in account:
                etapestry_data.tags = account["tags"]
            if "photos" in account:
                etapestry_data.photos = account["photos"]
            if "videos" in account:
                etapestry_data.videos = account["videos"]

            # update the existing account
            await ETapestryDatas.data_service.update_one(
                collection=ETapestryDatas.DB_COLLECTION_ETAPESTRY_DATA,
                query=jsonable_encoder(query_request),
                data=jsonable_encoder({"$set": jsonable_encoder(etapestry_data)}),
            )

        return etapestry_data

    @staticmethod
    async def read(
        data_id: Optional[PyObjectId] = None,
        repository_id: Optional[PyObjectId] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_key: str = "creation_time",
        sort_direction: int = -1,
        throw_on_not_found: bool = True,
    ) -> List[ETapestryData_Db]:
        etapestry_data_list = []

        query = {}
        if data_id:
            query["_id"] = str(data_id)
        if repository_id:
            query["repository_id"] = str(repository_id)

        # only read the non deleted ones
        query["state"] = ETapestryDataState.ACTIVE.value

        if skip is None and limit is None:
            response = await ETapestryDatas.data_service.find_by_query(
                collection=ETapestryDatas.DB_COLLECTION_ETAPESTRY_DATA,
                query=jsonable_encoder(query),
            )
        elif skip is not None and limit is not None:
            response = await ETapestryDatas.data_service.find_sorted_pagination(
                collection=ETapestryDatas.DB_COLLECTION_ETAPESTRY_DATA,
                query=jsonable_encoder(query),
                sort_key=sort_key,
                sort_direction=sort_direction,
                skip=skip,
                limit=limit,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both skip and limit need to be provided for pagination",
            )

        if response:
            for etapestry_data in response:
                etapestry_data_list.append(ETapestryData_Db(**etapestry_data))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No messages found for query: {query}",
            )

        return etapestry_data_list

    @staticmethod
    async def count(
        repository_id: Optional[PyObjectId] = None,
    ) -> int:
        query = {}
        if repository_id:
            query["repository_id"] = str(repository_id)

        return await ETapestryDatas.data_service.sail_db[ETapestryDatas.DB_COLLECTION_ETAPESTRY_DATA].count_documents(
            query
        )

    @staticmethod
    async def update(
        query_id: PyObjectId,
        update_state: Optional[ETapestryDataState] = None,
        update_notes: Optional[str] = None,
        update_tags: Optional[List[str]] = None,
        update_photos: Optional[List[PyObjectId]] = None,
        update_videos: Optional[List[PyObjectId]] = None,
        throw_on_no_update: bool = True,
    ):
        query = {}
        if query_id:
            query["_id"] = str(query_id)

        update_request = {"$set": {}}
        if update_state:
            update_request["$set"]["state"] = update_state.value
        if update_notes:
            update_request["$set"]["notes"] = update_notes
        if update_tags:
            update_request["$set"]["tags"] = update_tags
        if update_photos:
            update_request["$set"]["photos"] = update_photos
        if update_videos:
            update_request["$set"]["videos"] = update_videos

        update_response = await ETapestryDatas.data_service.update_one(
            collection=ETapestryDatas.DB_COLLECTION_ETAPESTRY_DATA,
            query=query,
            data=jsonable_encoder(update_request),
        )
        if update_response.modified_count == 0:
            if throw_on_no_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"ETapestry Data not found or no changes to update",
                )

    @staticmethod
    async def delete(
        data_id: Optional[PyObjectId] = None,
        repository_id: Optional[PyObjectId] = None,
    ):
        query = {}
        if data_id:
            query["_id"] = str(data_id)
        if repository_id:
            query["repository_id"] = str(repository_id)

        update_request = {"$set": {"state": ETapestryDataState.DELETED.value}}
        await ETapestryDatas.data_service.update_many(
            collection=ETapestryDatas.DB_COLLECTION_ETAPESTRY_DATA,
            query=query,
            data=jsonable_encoder(update_request),
        )
