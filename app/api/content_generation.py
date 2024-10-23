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

import traceback
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
from app.models.content_generation_template import ContentGenerationTemplate_Db, ContentGenerationTemplates, Context
from app.utils import log_manager
from app.utils.azure_openai import OpenAiGenerator
from app.utils.secrets import secret_store

router = APIRouter(prefix="/api/content-generations", tags=["content-generations"])


@router.post(
    path="/",
    description="Create a new content generation record",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="create_content_generation",
)
async def create_content_generation(
    content_generation: RegisterContentGeneration_In = Body(description="Content generation information"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterContentGeneration_Out:

    # Get the content generation template
    content_generation_template = await ContentGenerationTemplates.read(
        content_generation_template_id=content_generation.template_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )

    generated_content = await generate_content(content_generation, content_generation_template[0])

    content_generation_db = ContentGeneration_Db(
        template_id=content_generation.template_id,
        values=content_generation.values,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        generated=generated_content,
        state=ContentGenerationState.ACTIVE,
        creation_time=datetime.utcnow(),
    )

    await ContentGenerations.create(content_generation_db)

    return RegisterContentGeneration_Out(id=content_generation_db.id, generated=generated_content)


@router.post(
    path="/public",
    description="Create a new public content generation record",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="create_public_content_generation",
)
async def create_public_content_generation(
    content_generation: RegisterContentGeneration_In = Body(description="Content generation information"),
) -> RegisterContentGeneration_Out:

    content_generation_template = await ContentGenerationTemplates.read(
        content_generation_template_id=content_generation.template_id,
        is_public=True,
        throw_on_not_found=True,
    )

    generated_content = await generate_content(content_generation, content_generation_template[0])

    content_generation_db = ContentGeneration_Db(
        template_id=content_generation.template_id,
        values=content_generation.values,
        organization_id=content_generation_template[0].organization_id,
        generated=generated_content,
        state=ContentGenerationState.ACTIVE,
        creation_time=datetime.utcnow(),
    )

    await ContentGenerations.create(content_generation_db)

    return RegisterContentGeneration_Out(id=content_generation_db.id, generated=generated_content)


@router.get(
    path="/",
    description="Get all content generation records for a user",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
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
        organization_id=current_user.organization_id,
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
    response_model_by_alias=False,
)
async def get_content_generation(
    content_generation_id: PyObjectId = Path(description="Content generation record id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetContentGeneration_Out:

    content_generation = await ContentGenerations.read(
        content_generation_id=content_generation_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )
    if not content_generation:
        raise HTTPException(status_code=404, detail="Content generation not found")

    return GetContentGeneration_Out(**content_generation[0].dict())


async def generate_content(
    content_generation_req: RegisterContentGeneration_In, content_generation_template: ContentGenerationTemplate_Db
) -> str:
    try:
        # prepare the content generation messages
        messages = content_generation_template.context
        prompt = content_generation_template.prompt.format(**content_generation_req.values)

        messages.append(Context(role="user", content=prompt))
        messages = [message.dict() for message in messages]

        # Make a call to OpenAI to generate the content
        openai = OpenAiGenerator(secret_store.OPENAI_API_BASE, secret_store.OPENAI_API_KEY)
        generated_content = await openai.get_response(messages=messages)

        return generated_content
    except Exception as e:
        error_id = str(PyObjectId())
        log_manager.ERROR(
            {
                "message": f"Error while generating content: {e}",
                "stack_trace": traceback.format_exc(),
                "error_id": error_id,
            }
        )
        raise HTTPException(
            status_code=500, detail=f"Error while generating content. Please try again later. Error ID: {error_id}"
        )
