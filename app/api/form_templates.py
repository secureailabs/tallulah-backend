# -------------------------------------------------------------------------------
# Engineering
# form_templates.py
# -------------------------------------------------------------------------------
""" Service to manage form templates """
# -------------------------------------------------------------------------------
# Copyright (C) 2023 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------


from datetime import datetime

from fastapi import APIRouter, Body, Depends, Path, Response, status

from app.api.authentication import get_current_user
from app.models import organizations
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.form_templates import (
    FormTemplate_Db,
    FormTemplates,
    FormTemplateState,
    GetFormTemplate_Out,
    GetMultipleFormTemplate_Out,
    RegisterFormTemplate_In,
    RegisterFormTemplate_Out,
    UpdateFormTemplate_In,
)

router = APIRouter(prefix="/api/form-templates", tags=["form-templates"])


@router.post(
    path="/",
    description="Add a new form template",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_new_form_template",
)
async def add_new_form_template(
    form_template: RegisterFormTemplate_In = Body(description="Form template information"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterFormTemplate_Out:
    # Add the response template
    form_template_db = FormTemplate_Db(
        name=form_template.name,
        description=form_template.description,
        field_groups=form_template.field_groups,
        user_id=current_user.id,
        organization=current_user.organization,
    )
    await FormTemplates.create(form_template_db)

    return RegisterFormTemplate_Out(_id=form_template_db.id)


@router.get(
    path="/",
    description="Get all the response templates for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_all_form_templates",
)
async def get_all_form_templates(
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleFormTemplate_Out:
    form_templates = await FormTemplates.read(organization=current_user.organization, throw_on_not_found=False)

    return GetMultipleFormTemplate_Out(
        templates=[GetFormTemplate_Out(**template.dict()) for template in form_templates]
    )


@router.get(
    path="/{form_template_id}",
    description="Get the response template for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_form_template",
)
async def get_form_template(
    form_template_id: PyObjectId = Path(description="Form template id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetFormTemplate_Out:
    form_template = await FormTemplates.read(
        template_id=form_template_id, organization=current_user.organization, throw_on_not_found=True
    )

    return GetFormTemplate_Out(**form_template[0].dict())


@router.get(
    path="/published/{form_template_id}",
    description="Get the response template for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_published_form_template",
)
async def get_published_form_template(
    form_template_id: PyObjectId = Path(description="Form template id"),
) -> GetFormTemplate_Out:
    form_template = await FormTemplates.read(
        template_id=form_template_id, state=FormTemplateState.PUBLISHED, throw_on_not_found=True
    )

    return GetFormTemplate_Out(**form_template[0].dict())


@router.patch(
    path="/{form_template_id}",
    description="Update the response template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="update_form_template",
)
async def update_form_template(
    form_template_id: PyObjectId = Path(description="Form template id"),
    form_template: UpdateFormTemplate_In = Body(description="Form template information"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Update the response template
    await FormTemplates.update(
        query_form_template_id=form_template_id,
        query_organization=current_user.organization,
        update_form_template_name=form_template.name,
        update_form_template_description=form_template.description,
        update_form_template_field_groups=form_template.field_groups,
        udpate_form_template_card_layout=form_template.card_layout,
        update_form_template_logo=form_template.logo,
        update_form_template_last_edit_time=datetime.utcnow(),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    path="/{form_template_id}/publish",
    description="Update the response template state for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="publish_form_template",
)
async def publish_form_template(
    form_template_id: PyObjectId = Path(description="Form template id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Update the response template
    await FormTemplates.update(
        query_form_template_id=form_template_id,
        query_organization=current_user.organization,
        update_form_template_state=FormTemplateState.PUBLISHED,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    path="/{form_template_id}",
    description="Delete the response template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_form_template",
)
async def delete_form_template(
    form_template_id: PyObjectId = Path(description="Form template id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Delete the response template
    await FormTemplates.update(
        query_form_template_id=form_template_id,
        query_organization=current_user.organization,
        update_form_template_state=FormTemplateState.DELETED,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
