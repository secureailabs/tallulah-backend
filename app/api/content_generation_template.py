# -------------------------------------------------------------------------------
# Engineering
# content_generation_template.py
# -------------------------------------------------------------------------------
""" Service to manage content generation templates """
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
from app.models.content_generation_template import (
    ContentGenerationState,
    ContentGenerationTemplate_Base,
    ContentGenerationTemplate_Db,
    ContentGenerationTemplates,
    GetContentGenerationTemplate_Out,
    GetMultipleContentGenerationTemplate_Out,
    RegisterContentGenerationTemplate_Out,
    UpdateContentGenerationTemplate_In,
)

router = APIRouter(prefix="/api/content-generation-templates", tags=["content-generation-templates"])


@router.post(
    path="/",
    description="Add a new content generation template",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_new_content_generation_template",
)
async def add_new_content_generation_template(
    content_generation_template: ContentGenerationTemplate_Base = Body(
        description="Content generation template information"
    ),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterContentGenerationTemplate_Out:

    # Add the content generation template
    content_generation_template_db = ContentGenerationTemplate_Db(
        name=content_generation_template.name,
        description=content_generation_template.description,
        parameters=content_generation_template.parameters,
        context=content_generation_template.context,
        prompt=content_generation_template.prompt,
        user_id=current_user.id,
        organization=current_user.organization,
        state=ContentGenerationState.ACTIVE,
    )
    await ContentGenerationTemplates.create(content_generation_template_db)

    return RegisterContentGenerationTemplate_Out(id=content_generation_template_db.id)


@router.get(
    path="/",
    description="Get all content generation templates for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_all_content_generation_templates",
)
async def get_all_content_generation_templates(
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleContentGenerationTemplate_Out:

    content_generation_templates = await ContentGenerationTemplates.read(
        organization=current_user.organization, throw_on_not_found=False
    )

    return GetMultipleContentGenerationTemplate_Out(
        templates=[GetContentGenerationTemplate_Out(**template.dict()) for template in content_generation_templates]
    )


@router.get(
    path="/{content_generation_template_id}",
    description="Get a specific content generation template for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_content_generation_template",
)
async def get_content_generation_template(
    content_generation_template_id: PyObjectId = Path(description="Content generation template id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetContentGenerationTemplate_Out:

    content_generation_template = await ContentGenerationTemplates.read(
        content_generation_template_id=content_generation_template_id,
        organization=current_user.organization,
        throw_on_not_found=True,
    )

    return GetContentGenerationTemplate_Out(**content_generation_template[0].dict())


@router.patch(
    path="/{content_generation_template_id}",
    description="Update a content generation template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="update_content_generation_template",
)
async def update_content_generation_template(
    content_generation_template_id: PyObjectId = Path(description="Content generation template id"),
    content_generation_template: UpdateContentGenerationTemplate_In = Body(
        description="Content generation template information"
    ),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Update the content generation template
    await ContentGenerationTemplates.update(
        query_content_generation_template_id=content_generation_template_id,
        query_organization=current_user.organization,
        update_content_generation_template_name=content_generation_template.name,
        update_content_generation_template_description=content_generation_template.description,
        update_content_generation_template_parameters=content_generation_template.parameters,
        update_content_generation_template_context=content_generation_template.context,
        update_content_generation_template_prompt=content_generation_template.prompt,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    path="/{content_generation_template_id}",
    description="Delete a content generation template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_content_generation_template",
)
async def delete_content_generation_template(
    content_generation_template_id: PyObjectId = Path(description="Content generation template id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Delete the content generation template
    await ContentGenerationTemplates.update(
        query_content_generation_template_id=content_generation_template_id,
        query_organization=current_user.organization,
        update_content_generation_template_state=ContentGenerationState.DELETED,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
