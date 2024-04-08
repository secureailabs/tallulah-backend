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
from typing import List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class PatientProfileState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class Guardian(SailBaseModel):
    relationship: StrictStr = Field()
    name: StrictStr = Field()
    employer: StrictStr = Field()
    email: StrictStr = Field()
    phone: StrictStr = Field()


class PatientRequests(SailBaseModel):
    id: PyObjectId = Field()
    purpose: StrictStr = Field()


class PatientProfile_Base(SailBaseModel):
    patient_id: PyObjectId = Field()
    repository_id: PyObjectId = Field()
    name: StrictStr = Field()
    primary_cancer_diagnosis: StrictStr = Field()
    social_worker_name: StrictStr = Field()
    social_worker_organization: StrictStr = Field()
    date_of_diagnosis: str = Field()
    age: int = Field()
    guardians: List[Guardian] = Field()
    household_details: str = Field()
    family_net_monthly_income: int = Field()
    address: str = Field()
    recent_requests: List[PatientRequests] = Field()


class PatientProfile_Db(PatientProfile_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    state: PatientProfileState = Field(default=PatientProfileState.ACTIVE)
    organization: StrictStr = Field()
    owner_id: PyObjectId = Field()


class RegisterPatientProfile_In(PatientProfile_Base):
    pass


class RegisterPatientProfile_Out(SailBaseModel):
    id: PyObjectId = Field()


class GetPatientProfile_Out(PatientProfile_Base):
    id: PyObjectId = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    state: PatientProfileState = Field(default=PatientProfileState.ACTIVE)
    organization: StrictStr = Field()
    owner_id: PyObjectId = Field()


class UpdatePatientProfile_In(SailBaseModel):
    name: StrictStr = Field()
    primary_cancer_diagnosis: StrictStr = Field()
    social_worker_name: StrictStr = Field()
    social_worker_organization: StrictStr = Field()
    date_of_diagnosis: str = Field()
    age: int = Field()
    guardians: List[Guardian] = Field()
    household_details: str = Field()
    family_net_monthly_income: int = Field()
    address: str = Field()
    recent_requests: List[PatientRequests] = Field()


class GetMultiplePatientProfiles_Out(SailBaseModel):
    count: int = Field()
    next: int = Field(default=0)
    limit: int = Field(default=10)
    patient_profiles: List[GetPatientProfile_Out] = Field()


class PatientProfiles:
    DB_COLLECTION_PATIENT_PROFILES = "patient_profiles"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        patient_profile: PatientProfile_Db,
    ):
        return await PatientProfiles.data_service.insert_one(
            collection=PatientProfiles.DB_COLLECTION_PATIENT_PROFILES,
            data=jsonable_encoder(patient_profile),
        )

    @staticmethod
    async def read(
        patient_profile_id: Optional[PyObjectId] = None,
        patient_id: Optional[PyObjectId] = None,
        repository_id: Optional[PyObjectId] = None,
        owner_id: Optional[PyObjectId] = None,
        organization: Optional[StrictStr] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_key: str = "creation_time",
        sort_direction: int = -1,
        throw_on_not_found: bool = True,
    ) -> List[PatientProfile_Db]:
        patient_profile_list = []

        query = {}
        if repository_id:
            query["repository_id"] = str(repository_id)
        if owner_id:
            query["owner_id"] = str(owner_id)
        if organization:
            query["organization"] = organization
        if patient_profile_id:
            query["_id"] = str(patient_profile_id)
        if patient_id:
            query["patient_id"] = str(patient_id)

        # Only read the ACTIVE patient profiles
        query["state"] = PatientProfileState.ACTIVE.value

        if skip is None and limit is None:
            response = await PatientProfiles.data_service.find_by_query(
                collection=PatientProfiles.DB_COLLECTION_PATIENT_PROFILES, query=jsonable_encoder(query)
            )
        elif skip is not None and limit is not None:
            response = await PatientProfiles.data_service.find_sorted_pagination(
                collection=PatientProfiles.DB_COLLECTION_PATIENT_PROFILES,
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
            for patient_profile in response:
                patient_profile_list.append(PatientProfile_Db(**patient_profile))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No patient story found for query: {query}",
            )

        return patient_profile_list

    @staticmethod
    async def count(
        repository_id: Optional[PyObjectId] = None,
    ) -> int:
        query = {}
        if repository_id:
            query["repository_id"] = str(repository_id)

        return await PatientProfiles.data_service.sail_db[
            PatientProfiles.DB_COLLECTION_PATIENT_PROFILES
        ].count_documents(query)

    @staticmethod
    async def update(
        query_patient_profile_id: Optional[PyObjectId] = None,
        query_organization: Optional[StrictStr] = None,
        update_patient_profile_state: Optional[PatientProfileState] = None,
        update_patient_profile: Optional[UpdatePatientProfile_In] = None,
    ):
        query = {}
        if query_patient_profile_id:
            query["_id"] = str(query_patient_profile_id)
        if query_organization:
            query["organization"] = query_organization

        update = {}
        if update_patient_profile_state:
            update["state"] = update_patient_profile_state.value
        if update_patient_profile:
            update["name"] = update_patient_profile.name
            update["primary_cancer_diagnosis"] = update_patient_profile.primary_cancer_diagnosis
            update["social_worker_name"] = update_patient_profile.social_worker_name
            update["social_worker_organization"] = update_patient_profile.social_worker_organization
            update["date_of_diagnosis"] = update_patient_profile.date_of_diagnosis
            update["age"] = update_patient_profile.age
            update["guardians"] = update_patient_profile.guardians
            update["household_details"] = update_patient_profile.household_details
            update["family_net_monthly_income"] = update_patient_profile.family_net_monthly_income
            update["address"] = update_patient_profile.address
            update["recent_requests"] = update_patient_profile.recent_requests

        update_result = await PatientProfiles.data_service.update_one(
            collection=PatientProfiles.DB_COLLECTION_PATIENT_PROFILES,
            query=jsonable_encoder(query),
            data=jsonable_encoder({"$set": update}),
        )

        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PatientProfile not found for query: {query}",
            )
