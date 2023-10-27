# -------------------------------------------------------------------------------
# Engineering
# response_templates.py
# -------------------------------------------------------------------------------
""" Service to manage response templates """
# -------------------------------------------------------------------------------
# Copyright (C) 2023 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------


import time
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response, status

from app.api.authentication import get_current_user
from app.api.emails import read_emails
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.email import Emails
from app.models.response_templates import (
    GetMultipleResponseTemplate_Out,
    GetResponseTemplate_Out,
    RegisterResponseTemplate_In,
    RegisterResponseTemplate_Out,
    ResponseTemplate_Base,
    ResponseTemplate_Db,
    ResponseTemplates,
    UpdateResponseTemplate_In,
)
from app.utils.background_couroutines import AsyncTaskManager
from app.utils.emails import OutlookClient
from app.utils.secrets import delete_keyvault_secret, set_keyvault_secret

router = APIRouter(prefix="/response-templates", tags=["response-templates"])


@router.post(
    path="/",
    description="Add a new resposne template",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_new_response_template",
)
async def add_new_response_template(
    response_template: RegisterResponseTemplate_In = Body(description="Response template information"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterResponseTemplate_Out:
    # Add the response template
    response_template_db = ResponseTemplate_Db(
        name=response_template.name,
        subject=response_template.subject,
        body=response_template.body,
        user_id=current_user.id,
    )
    await ResponseTemplates.create(response_template_db)

    return RegisterResponseTemplate_Out(_id=response_template_db.id)


@router.get(
    path="/",
    description="Get all the response templates for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_all_response_templates",
)
async def get_all_response_templates(
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleResponseTemplate_Out:
    response_templates = await ResponseTemplates.read(user_id=current_user.id, throw_on_not_found=False)

    return GetMultipleResponseTemplate_Out(
        templates=[GetResponseTemplate_Out(**template.dict()) for template in response_templates]
    )


@router.get(
    path="/{response_template_id}",
    description="Get the response template for the current user",
    status_code=status.HTTP_200_OK,
    operation_id="get_response_template",
)
async def get_response_template(
    response_template_id: PyObjectId = Path(description="Response template id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetResponseTemplate_Out:
    response_template = await ResponseTemplates.read(
        template_id=response_template_id, user_id=current_user.id, throw_on_not_found=True
    )

    return GetResponseTemplate_Out(**response_template[0].dict())


@router.patch(
    path="/{response_template_id}",
    description="Update the response template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="update_response_template",
)
async def update_response_template(
    response_template_id: PyObjectId = Path(description="Response template id"),
    response_template: UpdateResponseTemplate_In = Body(description="Response template information"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Update the response template
    await ResponseTemplates.update(
        query_response_template_id=response_template_id,
        query_user_id=current_user.id,
        update_response_template_subject=response_template.subject,
        update_response_template_body=response_template.body,
        update_response_template_note=response_template.note,
        update_response_template_last_edit_time=datetime.utcnow(),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    path="/{response_template_id}",
    description="Delete the response template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_response_template",
)
async def delete_response_template(
    response_template_id: PyObjectId = Path(description="Response template id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Delete the response template
    await ResponseTemplates.delete(query_response_template_id=response_template_id, query_user_id=current_user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
