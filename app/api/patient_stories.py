# -------------------------------------------------------------------------------
# Engineering
# patient_stories.py
# -------------------------------------------------------------------------------
""" Service to manage patient stories """
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
from app.models.common import PyObjectId
from app.models.patient_stories import (
    GetMultiplePatientStories_Out,
    GetPatientStory_Out,
    PatientStories,
    PatientStory_Db,
    RegisterPatientStory_In,
    RegisterPatientStory_Out,
)

router = APIRouter(prefix="/api/patient-stories", tags=["patient-stories"])


@router.post(
    path="/",
    description="Add a new patient story",
    status_code=status.HTTP_200_OK,
    operation_id="add_new_patient_story",
)
async def add_new_patient_story(
    patient_story: RegisterPatientStory_In = Body(description="Patient story information"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterPatientStory_Out:
    # Create the patient story and add it to the database
    patient_story_db = PatientStory_Db(
        patient=patient_story.patient,
        story=patient_story.story,
        owner_id=current_user.id,
    )

    return RegisterPatientStory_Out(_id=patient_story_db.id)


@router.get(
    path="/",
    description="Get all the patient stories owned by the current user with pagination",
    status_code=status.HTTP_200_OK,
    operation_id="get_all_patient_stories",
)
async def get_all_patient_stories(
    skip: int = Query(default=0, description="Number of patient stories to skip"),
    limit: int = Query(default=20, description="Number of patient stories to return"),
    sort_key: str = Query(default="creation_time", description="Sort key"),
    sort_direction: int = Query(default=-1, description="Sort direction"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultiplePatientStories_Out:
    patient_stories = await PatientStories.read(
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
        throw_on_not_found=False,
    )

    story_count = await PatientStories.count(owner_id=current_user.id)

    return GetMultiplePatientStories_Out(
        patient_stories=[GetPatientStory_Out(**stories.dict()) for stories in patient_stories],
        count=story_count,
        next=skip + limit,
        limit=limit,
    )
