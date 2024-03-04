# -------------------------------------------------------------------------------
# Engineering
# patient_stories.py
# -------------------------------------------------------------------------------
"""Patient stories models used to manage patient stories"""
# -------------------------------------------------------------------------------
# Copyright (C) 2023 Array Insights, Inc. All Rights Reserved.
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


class PatientProfileState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class PatientProfile_Base(SailBaseModel):
    patient: Dict = Field()
    story: StrictStr = Field()
    owner_id: PyObjectId = Field()


class PatientProfile_Db(PatientProfile_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    state: PatientProfileState = Field(default=PatientProfileState.ACTIVE)


class GetPatientProfile_Out(PatientProfile_Base):
    id: PyObjectId = Field(alias="_id")
    creation_time: datetime = Field()


class RegisterPatientProfile_In(PatientProfile_Base):
    pass


class RegisterPatientProfile_Out(SailBaseModel):
    id: PyObjectId = Field(alias="_id")


class GetMultiplePatientProfiles_Out(SailBaseModel):
    count: int = Field()
    next: int = Field(default=0)
    limit: int = Field(default=10)
    patient_stories: List[GetPatientProfile_Out] = Field()


class PatientProfiles:
    DB_COLLECTION_PATIENT_STORIES = "patient_stories"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        mailbox: PatientProfile_Db,
    ):
        return await PatientProfiles.data_service.insert_one(
            collection=PatientProfiles.DB_COLLECTION_PATIENT_STORIES,
            data=jsonable_encoder(mailbox),
        )

    @staticmethod
    async def read(
        patient_story_id: Optional[PyObjectId] = None,
        patient_story_id_list: Optional[List[PyObjectId]] = None,
        owner_id: Optional[PyObjectId] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_key: str = "creation_time",
        sort_direction: int = -1,
        throw_on_not_found: bool = True,
    ) -> List[PatientProfile_Db]:
        patient_story_list = []

        query = {}
        if patient_story_id:
            query["_id"] = str(patient_story_id)
        elif patient_story_id_list:
            query["_id"] = {"$in": [str(patient_story_id) for patient_story_id in patient_story_id_list]}
        else:
            raise Exception("Provide either patient_story_id or patient_story_id_list")

        if owner_id:
            query["owner_id"] = str(owner_id)

        if skip is None and limit is None:
            response = await PatientProfiles.data_service.find_by_query(
                collection=PatientProfiles.DB_COLLECTION_PATIENT_STORIES, query=jsonable_encoder(query)
            )
        elif skip is not None and limit is not None:
            response = await PatientProfiles.data_service.find_sorted_pagination(
                collection=PatientProfiles.DB_COLLECTION_PATIENT_STORIES,
                query=jsonable_encoder(query),
                skip=skip,
                limit=limit,
                sort_key=sort_key,
                sort_direction=sort_direction,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid skip and limit values: skip={skip}, limit={limit}",
            )

        if response:
            for patient_story in response:
                patient_story_list.append(PatientProfile_Db(**patient_story))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No patient story found for query: {query}",
            )

        return patient_story_list

    @staticmethod
    async def count(owner_id: Optional[PyObjectId] = None) -> int:
        query = {}
        if owner_id:
            query["owner_id"] = str(owner_id)

        return await PatientProfiles.data_service.sail_db[
            PatientProfiles.DB_COLLECTION_PATIENT_STORIES
        ].count_documents(query)

    @staticmethod
    async def update(
        query_patient_story_id: Optional[PyObjectId] = None,
        update_patient_story_state: Optional[PatientProfileState] = None,
    ):
        query = {}
        if query_patient_story_id:
            query["_id"] = str(query_patient_story_id)

        update = {}
        if update_patient_story_state:
            update["state"] = update_patient_story_state.value

        update_result = await PatientProfiles.data_service.update_one(
            collection=PatientProfiles.DB_COLLECTION_PATIENT_STORIES,
            query=jsonable_encoder(query),
            data=jsonable_encoder({"$set": update}),
        )

        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PatientProfile not found for query: {query}",
            )
