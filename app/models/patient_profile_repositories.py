# -------------------------------------------------------------------------------
# Engineering
# patient_profile_repository.py
# -------------------------------------------------------------------------------
"""Models used by patient profile repository service"""
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
from app.models.form_templates import CardLayout


class PatientProfileRepositoryState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class PatientProfileRepository_Base(SailBaseModel):
    name: str = Field()
    description: Optional[str] = Field(default=None)
    card_layout: Optional[CardLayout] = Field(default=None)


class PatientProfileRepository_Db(PatientProfileRepository_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    state: PatientProfileRepositoryState = Field(default=PatientProfileRepositoryState.ACTIVE)


class GetPatientProfileRepository_Out(PatientProfileRepository_Base):
    id: PyObjectId = Field()
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    creation_time: datetime = Field()
    state: PatientProfileRepositoryState = Field()


class GetMultiplePatientProfileRepository_Out(SailBaseModel):
    repositories: List[GetPatientProfileRepository_Out] = Field()


class RegisterPatientProfileRepository_In(PatientProfileRepository_Base):
    pass


class RegisterPatientProfileRepository_Out(SailBaseModel):
    id: PyObjectId = Field()


class UpdatePatientProfileRepository_In(SailBaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)


class PatientProfileRepositories:
    DB_COLLECTION_PATIENT_PROFILE_REPOSITORY = "patient-profile-repository"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        patient_profile_repository: PatientProfileRepository_Db,
    ):
        return await PatientProfileRepositories.data_service.insert_one(
            collection=PatientProfileRepositories.DB_COLLECTION_PATIENT_PROFILE_REPOSITORY,
            data=jsonable_encoder(patient_profile_repository),
        )

    @staticmethod
    async def read(
        patient_profile_repository_id: Optional[PyObjectId] = None,
        user_id: Optional[PyObjectId] = None,
        organization_id: Optional[PyObjectId] = None,
        throw_on_not_found: bool = True,
    ) -> List[PatientProfileRepository_Db]:
        patient_profile_repository_list = []

        query = {}
        if patient_profile_repository_id:
            query["_id"] = str(patient_profile_repository_id)
        if user_id:
            query["user_id"] = str(user_id)
        if organization_id:
            query["organization_id"] = str(organization_id)

        # Read only active patient profile repositories
        query["state"] = PatientProfileRepositoryState.ACTIVE.value

        response = await PatientProfileRepositories.data_service.find_by_query(
            collection=PatientProfileRepositories.DB_COLLECTION_PATIENT_PROFILE_REPOSITORY,
            query=jsonable_encoder(query),
        )

        if response:
            for patient_profile_repository in response:
                patient_profile_repository_list.append(PatientProfileRepository_Db(**patient_profile_repository))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No patient profile repository found for query: {query}",
            )

        return patient_profile_repository_list

    @staticmethod
    async def update(
        query_patient_profile_repository_id: Optional[PyObjectId] = None,
        query_organization_id: Optional[PyObjectId] = None,
        update_patient_profile_repository_name: Optional[str] = None,
        update_patient_profile_repository_state: Optional[PatientProfileRepositoryState] = None,
        update_patient_profile_repository_description: Optional[str] = None,
    ):
        query = {}
        if query_patient_profile_repository_id:
            query["_id"] = str(query_patient_profile_repository_id)
        if query_organization_id:
            query["organization_id"] = str(query_organization_id)

        update_request = {"$set": {}}
        if update_patient_profile_repository_name:
            update_request["$set"]["name"] = update_patient_profile_repository_name
        if update_patient_profile_repository_state:
            update_request["$set"]["state"] = update_patient_profile_repository_state.value
        if update_patient_profile_repository_description:
            update_request["$set"]["description"] = update_patient_profile_repository_description

        update_response = await PatientProfileRepositories.data_service.update_many(
            collection=PatientProfileRepositories.DB_COLLECTION_PATIENT_PROFILE_REPOSITORY,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient profile repository not found or no changes to update",
            )
