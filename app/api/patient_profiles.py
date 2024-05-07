# -------------------------------------------------------------------------------
# Engineering
# patient_profiles.py
# -------------------------------------------------------------------------------
""" Service to manage patient profiles """
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from fastapi import APIRouter, Body, Depends, Path, Query, Response, status
from fastapi.encoders import jsonable_encoder

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.patient_profile import (
    GetMultiplePatientProfiles_Out,
    GetPatientProfile_Out,
    PatientProfile_Db,
    PatientProfiles,
    PatientProfileState,
    RegisterPatientProfile_In,
    RegisterPatientProfile_Out,
    UpdatePatientProfile_In,
)
from app.models.patient_profile_repositories import PatientProfileRepositories
from app.utils.elastic_search import ElasticsearchClient

router = APIRouter(prefix="/api/patient-profiles", tags=["patient-profiles"])


@router.post(
    path="/",
    description="Add a new patient profile if it does not exist else replace the existing one",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="add_patient_profile",
)
async def add_new_patient_profile(
    patient_profile: RegisterPatientProfile_In = Body(description="Patient profile information"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterPatientProfile_Out:

    # Check if repository exists
    _ = await PatientProfileRepositories.read(
        patient_profile_repository_id=patient_profile.repository_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )

    # Create the patient story and add it to the database
    patient_profile_db = PatientProfile_Db(
        repository_id=patient_profile.repository_id,
        patient_id=patient_profile.patient_id,
        name=patient_profile.name,
        primary_cancer_diagnosis=patient_profile.primary_cancer_diagnosis,
        date_of_diagnosis=patient_profile.date_of_diagnosis,
        age=patient_profile.age,
        guardians=patient_profile.guardians,
        social_worker_name=patient_profile.social_worker_name,
        social_worker_organization=patient_profile.social_worker_organization,
        household_details=patient_profile.household_details,
        family_net_monthly_income=patient_profile.family_net_monthly_income,
        address=patient_profile.address,
        recent_requests=patient_profile.recent_requests,
        organization_id=current_user.organization_id,
        owner_id=current_user.id,
        state=PatientProfileState.ACTIVE,
    )

    patient_profile_id = await PatientProfiles.create(patient_profile_db)

    # Add the form data to elasticsearch for search
    elastic_client = ElasticsearchClient()
    await elastic_client.insert_document(
        index_name=str(patient_profile.repository_id),
        id=str(patient_profile_id),
        document=jsonable_encoder(patient_profile_db, exclude=set(["_id", "id"])),
    )

    return RegisterPatientProfile_Out(id=patient_profile_id)


@router.get(
    path="/",
    description="Get all the patient profiles owned by the current user with pagination",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_all_patient_profiles",
)
async def get_all_patient_profiles(
    repository_id: PyObjectId = Query(default=None, description="Patient Profile Repository id"),
    skip: int = Query(default=0, description="Number of patient profiles to skip"),
    limit: int = Query(default=20, description="Number of patient profiles to return"),
    sort_key: str = Query(default="creation_time", description="Sort key"),
    sort_direction: int = Query(default=-1, description="Sort direction"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultiplePatientProfiles_Out:

    patient_profiles = await PatientProfiles.read(
        repository_id=repository_id,
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
        throw_on_not_found=False,
    )

    profiles_count = await PatientProfiles.count(repository_id=repository_id)

    return GetMultiplePatientProfiles_Out(
        patient_profiles=[GetPatientProfile_Out(**profiles.dict()) for profiles in patient_profiles],
        count=profiles_count,
        next=skip + limit,
        limit=limit,
    )


@router.get(
    path="/search",
    description="Search the text from patient profiles for the current user for the template",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="search_patient_profiles",
)
async def search_patient_profiles(
    repository_id: PyObjectId = Query(description="Patient Profile Repository id"),
    search_query: str = Query(description="Search query"),
    skip: int = Query(default=0, description="Number of patient profiles to skip"),
    limit: int = Query(default=10, description="Number of patient profiles to return"),
    current_user: TokenData = Depends(get_current_user),
):
    # Check if the user is the owner of the response template
    _ = await PatientProfileRepositories.read(
        patient_profile_repository_id=repository_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )

    # Search the form data
    elastic_client = ElasticsearchClient()
    response = await elastic_client.search(
        index_name=str(repository_id), search_query=search_query, size=limit, skip=skip
    )

    return response


@router.get(
    path="/{patient_profile_id}",
    description="Get a patient profile by id",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_patient_profile",
)
async def get_patient_profile(
    patient_profile_id: PyObjectId = Path(description="Patient profile id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetPatientProfile_Out:

    patient_profile = await PatientProfiles.read(
        organization_id=current_user.organization_id,
        patient_profile_id=patient_profile_id,
        throw_on_not_found=True,
    )

    # Check if the user is the owner of the response template
    _ = await PatientProfileRepositories.read(
        patient_profile_repository_id=patient_profile[0].repository_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )

    return GetPatientProfile_Out(**patient_profile[0].dict())


@router.put(
    path="/{patient_profile_id}",
    description="Update a patient profile by id",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="update_patient_profile",
)
async def update_patient_profile(
    patient_profile_id: PyObjectId = Path(description="Patient profile id"),
    patient_profile: UpdatePatientProfile_In = Body(description="Patient profile information"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:

    await PatientProfiles.update(
        query_patient_profile_id=patient_profile_id,
        query_organization_id=current_user.organization_id,
        update_patient_profile=patient_profile,
    )

    updated_patient_profile = await PatientProfiles.read(
        organization_id=current_user.organization_id,
        patient_profile_id=patient_profile_id,
        throw_on_not_found=True,
    )

    # Update the form data in elasticsearch for search
    elastic_client = ElasticsearchClient()
    await elastic_client.update_document(
        index_name=str(updated_patient_profile[0].repository_id),
        id=str(patient_profile_id),
        document=jsonable_encoder(updated_patient_profile[0], exclude=set(["_id", "id"])),
    )

    return Response(status_code=status.HTTP_200_OK)


@router.delete(
    path="/{patient_profile_id}",
    description="Delete a patient profile by id",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="delete_patient_profile",
)
async def delete_patient_profile(
    patient_profile_id: PyObjectId = Path(description="Patient profile id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:

    # Get the patient profile to check if the user is the owner of the patient profile
    patient_profile = await PatientProfiles.read(
        organization_id=current_user.organization_id,
        patient_profile_id=patient_profile_id,
        throw_on_not_found=True,
    )

    await PatientProfiles.update(
        query_patient_profile_id=patient_profile_id,
        query_organization_id=current_user.organization_id,
        update_patient_profile_state=PatientProfileState.DELETED,
    )

    # Delete the form data from elasticsearch for search
    elastic_client = ElasticsearchClient()
    await elastic_client.delete_document(index_name=str(patient_profile[0].repository_id), id=str(patient_profile_id))

    return Response(status_code=status.HTTP_200_OK)
