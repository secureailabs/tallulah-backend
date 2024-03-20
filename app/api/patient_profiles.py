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

from fastapi import APIRouter, Body, Depends, Query, status

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.patient_profile import (
    GetMultiplePatientProfiles_Out,
    GetPatientProfile_Out,
    PatientProfile_Db,
    PatientProfiles,
    RegisterPatientProfile_In,
    RegisterPatientProfile_Out,
)

router = APIRouter(prefix="/api/patient-profiles", tags=["patient-profiles"])


@router.post(
    path="/",
    description="Add a new patient profile",
    status_code=status.HTTP_200_OK,
    operation_id="add_patient_profile",
)
async def add_new_patient_profile(
    patient_profile: RegisterPatientProfile_In = Body(description="Patient profile information"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterPatientProfile_Out:

    # Create the patient story and add it to the database
    patient_profile_db = PatientProfile_Db(
        _id=patient_profile.id,
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
        organization=current_user.organization,
        owner_id=current_user.id,
    )

    await PatientProfiles.create(patient_profile_db)

    return RegisterPatientProfile_Out(_id=patient_profile_db.id)


@router.get(
    path="/",
    description="Get all the patient profiles owned by the current user with pagination",
    status_code=status.HTTP_200_OK,
    operation_id="get_all_patient_profiles",
)
async def get_all_patient_profiles(
    skip: int = Query(default=0, description="Number of patient profiles to skip"),
    limit: int = Query(default=20, description="Number of patient profiles to return"),
    sort_key: str = Query(default="creation_time", description="Sort key"),
    sort_direction: int = Query(default=-1, description="Sort direction"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultiplePatientProfiles_Out:

    patient_profiles = await PatientProfiles.read(
        organization=current_user.organization,
        skip=skip,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
        throw_on_not_found=False,
    )

    story_count = await PatientProfiles.count(owner_id=current_user.id)

    return GetMultiplePatientProfiles_Out(
        patient_profiles=[GetPatientProfile_Out(**profiles.dict()) for profiles in patient_profiles],
        count=story_count,
        next=skip + limit,
        limit=limit,
    )
