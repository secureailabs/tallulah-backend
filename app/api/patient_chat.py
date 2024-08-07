# -------------------------------------------------------------------------------
# Engineering
# patient_chat.py
# -------------------------------------------------------------------------------
"""APIs used for patient chat"""
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime

from app.models.form_templates import FormTemplates
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Response, status
from fastapi_utils.tasks import repeat_every

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.form_data import FormDatas
from app.models.patient_profile import (
    PatientProfile_Base,
    PatientProfiles,
)
from app.models.patient_chat import (
    PatientChat,
    PatientChat_Base,
    PatientChat_Out,
    PatientChat_Db,
    PatientChatTemplates,
)
from app.models.content_generation_template import Context
from app.utils.azure_openai import OpenAiGenerator
from app.utils.secrets import secret_store

router = APIRouter(prefix="/api/patient-chat", tags=["patient-chat"])

@router.post(
    path="/",
    description="Start patient chat",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="start_patient_chat",
)
async def start_patient_chat(
    patient: PatientChat_Base = Body(description="Patient Id and Template Id"),
    current_user: TokenData = Depends(get_current_user),
) -> PatientChat_Out:

    # Check patient access for organization / form
    forms = await FormDatas.read(form_data_id=patient.form_data_id)
    if not forms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient form not found",
        )

    form_template = await FormTemplates.read(template_id=forms[0].form_template_id)
    if not form_template or form_template[0].organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient form not found",
        )

    # Check if chat exists
    chat = await PatientChat.get_chat(
        current_user.id,
        current_user.organization_id,
        patient.form_data_id,
    )

    if chat:
        return PatientChat_Out(id=chat.id, chat=chat.chat)

    # If not, create a new chat
    patient_chat = PatientChat_Db(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        form_data_id=patient.form_data_id,
        creation_time=datetime.utcnow(),
    )

    await PatientChat.create(patient_chat)

    return PatientChat_Out(id=patient_chat.id, chat=[])


@router.post(
    path="/{chat_id}",
    description="Ask a query",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="patient_chat",
)
async def patient_chat(
    chat_id: PyObjectId = Path(description="Chat Id"),
    query: str = Body(description="Query"),
    current_user: TokenData = Depends(get_current_user),
) -> PatientChat_Out:

    system_prompt = """
        You are an AI assistant that works with a patient advocacy organization.
        You are skilled at creating patient stories, fundraising emails, and personal emails or letters from data provided to you.
        You craft these letters or emails based on patient information, highlighting the patients' personal journeys and what is
        important to the patient in order to foster a sense of connection from the organization’s followers.
        You do not include any personally identifiable information other than the person’s name, their state if applicable,
        their diagnosis and their current disease state. You do not use full names and you do not use any financial information.
        You do not embellish upon the information given to you and you do not sensationalize or use cliches.
    """
    # TODO: Avoid parallel chat on the same chat_id
    chat = await PatientChat.get_chat_by_id(chat_id)

    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat not found")

    form_data = await FormDatas.read(form_data_id=chat.form_data_id)
    if not form_data:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = FormDatas.convert_form_data_to_string(form_data[0])

    if not chat.chat:
        chat.chat = [Context(role="user", content=patient)]

    conversation=[Context(role="system", content=system_prompt)]
    conversation.extend(chat.chat)
    conversation.append(Context(role="user", content=query))
    messages = [message.dict() for message in conversation]

    openai = OpenAiGenerator(secret_store.OPENAI_API_BASE, secret_store.OPENAI_API_KEY)
    generated_content = await openai.get_response(messages=messages)
    conversation.append(Context(role="assistant", content=generated_content))

    chat.chat = conversation[1:]
    await PatientChat.update(chat_id, chat)

    return PatientChat_Out(id=chat.id, chat=conversation[1:])


@router.get(
    path="/test/init",
    description="Initialize test data",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="init_data",
)
async def init_data(
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    await PatientChat.init_data(current_user.organization_id)

    return Response(status_code=status.HTTP_200_OK)
