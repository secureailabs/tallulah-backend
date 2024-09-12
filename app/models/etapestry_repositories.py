# -------------------------------------------------------------------------------
# Engineering
# etapestry_repository.py
# -------------------------------------------------------------------------------
"""Models used by eTapestry repository management service"""
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
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel
from app.models.form_templates import CardLayout


class ETapestryRepositoryState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class ETapestryRepository_Base(SailBaseModel):
    name: StrictStr = Field()
    description: StrictStr = Field()
    card_layout: Optional[CardLayout] = Field(default=None)


class RegisterETapestryRepository_In(ETapestryRepository_Base):
    database_name: StrictStr = Field()
    api_key: StrictStr = Field()


class RegisterETapestryRepository_Out(SailBaseModel):
    id: PyObjectId = Field()


class ETapestryRepository_Db(ETapestryRepository_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    state: ETapestryRepositoryState = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    last_refresh_time: datetime = Field()
    database_name_id: PyObjectId = Field()
    api_key_id: PyObjectId = Field()


class GetETapestryRepository_Out(ETapestryRepository_Base):
    id: PyObjectId = Field()
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    last_refresh_time: datetime = Field()
    state: ETapestryRepositoryState = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetMultipleETapestryRepository_Out(SailBaseModel):
    repositories: List[GetETapestryRepository_Out] = Field()


class UpdateETapestryRepository_In(SailBaseModel):
    name: Optional[StrictStr] = Field(default=None)
    description: Optional[StrictStr] = Field(default=None)
    card_layout: Optional[CardLayout] = Field(default=None)


class ETapestryRepositories:
    DB_COLLECTION_etapestry_REPOSITORIES = "etapestry_repositories"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        etapestry_repository: ETapestryRepository_Db,
    ):
        return await ETapestryRepositories.data_service.insert_one(
            collection=ETapestryRepositories.DB_COLLECTION_etapestry_REPOSITORIES,
            data=jsonable_encoder(etapestry_repository),
        )

    @staticmethod
    async def read(
        organization_id: Optional[PyObjectId] = None,
        repository_id: Optional[PyObjectId] = None,
        state: Optional[ETapestryRepositoryState] = None,
        throw_on_not_found: bool = True,
    ) -> List[ETapestryRepository_Db]:
        etapestry_repository_list = []

        query = {}
        if repository_id:
            query["_id"] = str(repository_id)
        if organization_id:
            query["organization_id"] = str(organization_id)
        if state:
            query["state"] = state.value
        else:
            query["state"] = {"$ne": ETapestryRepositoryState.DELETED.value}

        response = await ETapestryRepositories.data_service.find_by_query(
            collection=ETapestryRepositories.DB_COLLECTION_etapestry_REPOSITORIES,
            query=jsonable_encoder(query),
        )

        if response:
            for etapestry_repository in response:
                etapestry_repository_list.append(ETapestryRepository_Db(**etapestry_repository))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No messages found for query: {query}",
            )

        return etapestry_repository_list

    @staticmethod
    async def update(
        query_etapestry_repository_id: Optional[PyObjectId] = None,
        query_organization_id: Optional[PyObjectId] = None,
        update_etapestry_repository_name: Optional[StrictStr] = None,
        update_etapestry_repository_state: Optional[ETapestryRepositoryState] = None,
        update_etapestry_repository_description: Optional[StrictStr] = None,
        update_etapestry_repository_card_layout: Optional[CardLayout] = None,
        update_last_refresh_time: Optional[datetime] = None,
    ):
        query = {}
        if query_etapestry_repository_id:
            query["_id"] = str(query_etapestry_repository_id)
        if query_organization_id:
            query["organization_id"] = str(query_organization_id)

        update_request = {"$set": {}}
        if update_etapestry_repository_name:
            update_request["$set"]["name"] = update_etapestry_repository_name
        if update_etapestry_repository_description:
            update_request["$set"]["description"] = update_etapestry_repository_description
        if update_etapestry_repository_state:
            update_request["$set"]["state"] = update_etapestry_repository_state.value
        if update_etapestry_repository_card_layout:
            update_request["$set"]["card_layout"] = update_etapestry_repository_card_layout
        if update_last_refresh_time:
            update_request["$set"]["last_refresh_time"] = update_last_refresh_time

        update_response = await ETapestryRepositories.data_service.update_many(
            collection=ETapestryRepositories.DB_COLLECTION_etapestry_REPOSITORIES,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ETapestryRepository not found or no changes to update",
            )
