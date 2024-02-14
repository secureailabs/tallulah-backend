# -------------------------------------------------------------------------------
# Engineering
# content_generation.py
# -------------------------------------------------------------------------------
"""APIs used by content generation service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Response, status
from fastapi_utils.tasks import repeat_every

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.content_generation import (
    ContentGeneration_Db,
    ContentGenerations,
    ContentGenerationState,
    GetContentGeneration_Out,
    GetMultipleContentGeneration_Out,
    RegisterContentGeneration_In,
    RegisterContentGeneration_Out,
)

router = APIRouter(prefix="/api/content-generations", tags=["content-generations"])


@router.post(
    path="/",
    description="Create a new content generation record",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_content_generation",
)
async def create_content_generation(
    content_generation: RegisterContentGeneration_In = Body(description="Content generation information"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterContentGeneration_Out:

    content_generation_db = ContentGeneration_Db(
        template_id=content_generation.template_id,
        values=content_generation.values,
        user_id=current_user.id,
        organization=current_user.organization,
        creation_time=datetime.utcnow(),
    )

    await ContentGenerations.create(content_generation_db)

    return RegisterContentGeneration_Out(id=content_generation_db.id)


@router.get(
    path="/",
    description="Get all content generation records for a user",
    status_code=status.HTTP_200_OK,
    operation_id="get_all_content_generations",
)
async def get_all_content_generations(
    content_generation_template_id: PyObjectId = Query(description="Content generation template id"),
    skip: int = Query(description="Skip the first N records", default=0),
    limit: int = Query(description="Limit the number of records", default=50),
    sort_key: str = Query(description="Sort key", default="creation_time"),
    sort_direction: int = Query(description="Sort direction", default=-1),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleContentGeneration_Out:

    content_generations = await ContentGenerations.read(
        organization=current_user.organization,
        content_generation_template_id=content_generation_template_id,
        sort_key=sort_key,
        sort_direction=sort_direction,
        skip=skip,
        limit=limit,
        throw_on_not_found=False,
    )
    count = await ContentGenerations.count(content_generation_template_id=content_generation_template_id)

    return GetMultipleContentGeneration_Out(
        content_generations=[
            GetContentGeneration_Out(**content_generation.dict()) for content_generation in content_generations
        ],
        count=count,
        limit=limit,
        next=skip + limit,
    )


@router.get(
    path="/{content_generation_id}",
    description="Get a specific content generation record",
    status_code=status.HTTP_200_OK,
    operation_id="get_content_generation",
)
async def get_content_generation(
    content_generation_id: PyObjectId = Path(description="Content generation record id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetContentGeneration_Out:

    content_generation = await ContentGenerations.read(
        content_generation_id=content_generation_id,
        organization=current_user.organization,
        throw_on_not_found=True,
    )
    if not content_generation:
        raise HTTPException(status_code=404, detail="Content generation not found")

    return GetContentGeneration_Out(**content_generation[0].dict())


@router.post(
    path="/{content_generation_id}/retry",
    description="Retry a failed content generation record",
    status_code=status.HTTP_201_CREATED,
    operation_id="retry_content_generation",
)
async def retry_content_generation(
    content_generation_id: PyObjectId = Path(description="Content generation record id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:

    # Only retry failed content generation records
    content_generation = await ContentGenerations.read(
        content_generation_id=content_generation_id,
        content_generation_state=ContentGenerationState.ERROR,
        organization=current_user.organization,
        throw_on_not_found=True,
    )
    if not content_generation:
        raise HTTPException(status_code=404, detail="Content generation not found")

    # This is done by updating the state to received
    await ContentGenerations.update(
        query_content_generation_id=content_generation_id,
        update_state=ContentGenerationState.RECEIVED,
    )

    return Response(status_code=status.HTTP_201_CREATED)


@router.on_event("startup")
# 1 second interval between each run. No overlap as the next run will only start after the current run is finished
# This is done to prevent the open ai rate limiter from blocking the requests. Only 1 request per second will be processed
@repeat_every(seconds=1)
async def generate_content():

    # read the database to get the content generation object that is not processed yet and is the oldest one
    content_generation_req = await ContentGenerations.read(
        content_generation_state=ContentGenerationState.RECEIVED,
        skip=0,
        limit=1,
        sort_key="creation_time",
        sort_direction=1,
        throw_on_not_found=False,
    )

    if content_generation_req:
        content_generation_req = content_generation_req[0]

        # Update the state to processing
        await ContentGenerations.update(
            query_content_generation_id=content_generation_req.id,
            update_state=ContentGenerationState.PROCESSING,
        )

        # Make a call to OpenAI to generate the content
        try:
            # Update the state to processed
            await ContentGenerations.update(
                query_content_generation_id=content_generation_req.id,
                update_generated_content="Generated content from OpenAI",
                update_state=ContentGenerationState.DONE,
            )

        except Exception as e:
            # Update the state to failed
            await ContentGenerations.update(
                query_content_generation_id=content_generation_req.id,
                update_state=ContentGenerationState.ERROR,
                update_error_message=str(e),
            )
