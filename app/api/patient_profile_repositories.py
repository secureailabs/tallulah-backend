# -------------------------------------------------------------------------------
# Engineering
# patient_profile_repositories.py
# -------------------------------------------------------------------------------
""" Service to manage patient profile repositories """
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from fastapi import APIRouter, Body, Depends, Path, Response, status

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.patient_profile_repositories import (
    GetMultiplePatientProfileRepository_Out,
    GetPatientProfileRepository_Out,
    PatientProfileRepositories,
    PatientProfileRepository_Db,
    PatientProfileRepositoryState,
    RegisterPatientProfileRepository_In,
    RegisterPatientProfileRepository_Out,
    UpdatePatientProfileRepository_In,
)
from app.utils.elastic_search import ElasticsearchClient

router = APIRouter(prefix="/api/patient-profile-repositories", tags=["patient-profile-repositories"])


@router.post(
    path="/",
    description="Add a new patient profile repository",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="add_new_patient_profile_repository",
)
async def add_new_patient_profile_repository(
    patient_profile_repository: RegisterPatientProfileRepository_In = Body(
        description="Patient profile repository information"
    ),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterPatientProfileRepository_Out:

    # Add the patient profile repository
    patient_profile_repository_db = PatientProfileRepository_Db(
        name=patient_profile_repository.name,
        description=patient_profile_repository.description,
        user_id=current_user.id,
        organization=current_user.organization,
        card_layout=patient_profile_repository.card_layout,
        state=PatientProfileRepositoryState.ACTIVE,
    )
    await PatientProfileRepositories.create(patient_profile_repository_db)

    # Create index in elasticsearch
    elastic_client = ElasticsearchClient()
    await elastic_client.create_index(index_name=str(patient_profile_repository_db.id))

    return RegisterPatientProfileRepository_Out(id=patient_profile_repository_db.id)


@router.get(
    path="/",
    description="Get all patient profile repositories for the current user",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_all_patient_profile_repositories",
)
async def get_all_patient_profile_repositories(
    current_user: TokenData = Depends(get_current_user),
) -> GetMultiplePatientProfileRepository_Out:

    patient_profile_repositories = await PatientProfileRepositories.read(
        organization=current_user.organization, throw_on_not_found=False
    )

    return GetMultiplePatientProfileRepository_Out(
        repositories=[
            GetPatientProfileRepository_Out(**repository.dict()) for repository in patient_profile_repositories
        ]
    )


@router.get(
    path="/{patient_profile_repository_id}",
    description="Get a specific patient profile repository for the current user",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_patient_profile_repository",
)
async def get_patient_profile_repository(
    patient_profile_repository_id: PyObjectId = Path(description="Patient profile repository id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetPatientProfileRepository_Out:

    patient_profile_repository = await PatientProfileRepositories.read(
        patient_profile_repository_id=patient_profile_repository_id,
        organization=current_user.organization,
        throw_on_not_found=True,
    )

    return GetPatientProfileRepository_Out(**patient_profile_repository[0].dict())


@router.patch(
    path="/{patient_profile_repository_id}",
    description="Update a patient profile repository for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="update_patient_profile_repository",
)
async def update_patient_profile_repository(
    patient_profile_repository_id: PyObjectId = Path(description="Patient profile repository id"),
    patient_profile_repository: UpdatePatientProfileRepository_In = Body(
        description="Patient profile repository information"
    ),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Update the patient profile repository
    await PatientProfileRepositories.update(
        query_patient_profile_repository_id=patient_profile_repository_id,
        query_organization=current_user.organization,
        update_patient_profile_repository_name=patient_profile_repository.name,
        update_patient_profile_repository_description=patient_profile_repository.description,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    path="/{patient_profile_repository_id}",
    description="Delete a patient profile repository for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_patient_profile_repository",
)
async def delete_patient_profile_repository(
    patient_profile_repository_id: PyObjectId = Path(description="Patient profile repository id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Delete the patient profile repository
    await PatientProfileRepositories.update(
        query_patient_profile_repository_id=patient_profile_repository_id,
        query_organization=current_user.organization,
        update_patient_profile_repository_state=PatientProfileRepositoryState.DELETED,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
