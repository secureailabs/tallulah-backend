# -------------------------------------------------------------------------------
# Engineering
# patient_chat.py
# -------------------------------------------------------------------------------
"""Models used by patient chat service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------


from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel
from app.models.content_generation_template import Context
from app.utils.secrets import secret_store


class PatientChat_Base(SailBaseModel):
    form_data_id: PyObjectId = Field()


class PatientChat_Out(SailBaseModel):
    id: PyObjectId = Field()
    chat: Optional[List[Context]] = Field(default=None)


class PatientChat_Db(PatientChat_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()

    # generated: Optional[StrictStr] = Field(default=None)
    # state: ContentGenerationState = Field(default=ContentGenerationState.RECEIVED)
    # error_message: Optional[StrictStr] = Field(default=None)
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    updated_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    chat: Optional[List[Context]] = Field(default=None)


# class Context(SailBaseModel):
#     role: StrictStr = Field()
#     content: StrictStr = Field()


class PatientChatTemplate_Base(SailBaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    organization_id: PyObjectId = Field()
    template: StrictStr = Field()
    context: List[Context] = Field(default=None)


class PatientChatTemplates:
    DB_PATIENT_CHAT_TEMPLATES = "patient-chat-templates"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        template: PatientChatTemplate_Base,
    ):
        return await PatientChatTemplates.data_service.insert_one(
            collection=PatientChatTemplates.DB_PATIENT_CHAT_TEMPLATES,
            data=jsonable_encoder(template),
        )

    @staticmethod
    async def get_template(
        template_id: PyObjectId,
    ) -> Optional[PatientChatTemplate_Base]:
        template = await PatientChatTemplates.data_service.find_one(
            collection=PatientChatTemplates.DB_PATIENT_CHAT_TEMPLATES,
            query={
                "_id": str(template_id),
            },
        )
        if template:
            return PatientChatTemplate_Base(**template)
        return None

    @staticmethod
    async def get_all_templates() -> List[PatientChatTemplate_Base]:
        templates = await PatientChatTemplates.data_service.find_all(
            collection=PatientChatTemplates.DB_PATIENT_CHAT_TEMPLATES,
        )
        return [PatientChatTemplate_Base(**template) for template in templates]


class PatientChat:
    DB_PATIENT_CHAT = "patient-chat"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        patient_chat: PatientChat_Db,
    ):
        return await PatientChat.data_service.insert_one(
            collection=PatientChat.DB_PATIENT_CHAT,
            data=jsonable_encoder(patient_chat),
        )

    @staticmethod
    async def init_data(
        organization_id: PyObjectId,
    ):
        # Create Template
        # TODO: Fetch organization
        content = """
        You are an AI assistant that works with the Jay Fund. You are skilled at creating patient stories from data. You craft these letters based on patient information, highlighting the patients' personal journeys and what is important to the patient in order to foster a sense of connection from Jay Funds's followers. You use the style of this story: <Ashly is a bubbly, bright 12-year-old girl. She is the youngest of 4 children and is bilingual. She enjoys playing basketball and soccer. In September 2023 her whole world changed. Ashly was diagnosed with B-Cell acute lymphoblastic leukemia and treatment began immediately. A few weeks later on November 12 she was admitted for acute right sided weakness, she less alert and less verbal. MRI showed white matter changes consistent with the stroke-like side effects as a result of her treatment. Ashly's neuro status has improved since then. Also at that time, Ashly got a nasogastric tube (NG tube) to help with weight loss and inability to keep food down. As the month of November continued Ashly had multiple transfusions. Ashly has been doing better in December. She was able to attend the Jay Fund Christmas party and Family Hockey Night at the Icemen where she was able to visit with friends and drop the first puck at the hockey game. Ashly's mom, Helen describes Ashly as "a very tender girl, she always helps others, she is very noble, she loves to teach her classmates, she always defends the most vulnerable. She is an artist from a very young age, we noticed her ability to stand out in everything. She creates things from nothing which for me represents something useless and she already modifies it and creates something special."> Combined with the style and length of the story: <A whirlwind of chaos struck Ava's family on February 2, 2021. For weeks prior, 9-year-old Ava was suffering from fever, body aches and swollen lymph nodes, but tests for flu and COVID came back negative. With a massive snowstorm looming, Ava's mom, Stephanie, rushed her daughter to the emergency room to find answers… but the answer she got was crushing. Ava had T-cell acute lymphoblastic leukemia, a rare and aggressive cancer. Stephanie and her husband Robert were bombarded with rapid-fire details about treatment plans and procedures. Ava was rushed into the operating room for port implantation surgery and immediately began chemotherapy. For the next several months the family navigated a multitude of medical complications and hospital admissions. Stephanie spent countless nights in the hospital by Ava's bedside, isolated from Robert and her other daughter, Julianna. Just as the world slowly started to open back up during the pandemic, the family began a level of isolation that kept them completely separated from family and friends to protect Ava's compromised immune system. Job and income loss compounded the family's worries. After Stephanie took a leave of absence from work to care for Ava, Robert lost his position with a local public works department. The family blew through their savings. "We were buried in bills, but how do you leave your daughter's side when she is facing a life-threatening illness?" Stephanie asked. "The Jay Fund carried us through the most difficult part of the journey and paid our mortgage and utility bills to keep us afloat." Ava finally finished her chemotherapy treatment in July, and her family is looking forward to enjoying the rest of the summer. However, Ava still suffers from significant pain and debilitation, and she can no longer run and play like other kids. She will be undergoing intensive physical therapy to build her strength and stamina. "The chaos my family has lived through the past two years has been insane," Stephanie said. "At times it felt like there was an ocean between us and the rest of the world. But it has made us stronger and brought us closer."> You do not embellish upon the information given to you and you do not sensationalize or use cliches. You do not use full names and you do not use any financial information. Include a bit of backstory on the disease. Do not include any details about the patient that are not given to you.
        """
        template = PatientChatTemplate_Base(
            organization_id=organization_id,
            context=[Context(role="system", content=content)],
            template="Patient Name: {name}, Age: {age}, Guardians: {guardians}, Diagnosis: {primary_cancer_diagnosis}, Household Details: {household_details}",
        )
        # await PatientChatTemplates.create(template)

        # Add Indexes
        await PatientChat.data_service.create_index(
            collection=PatientChat.DB_PATIENT_CHAT, index=[("user_id", 1), ("form_data_id", 1)], unique=True
        )

    @staticmethod
    async def get_chat(
        user_id: PyObjectId,
        organization_id: PyObjectId,
        form_data_id: PyObjectId,
    ) -> Optional[PatientChat_Db]:
        chat = await PatientChat.data_service.find_one(
            collection=PatientChat.DB_PATIENT_CHAT,
            query={
                "user_id": str(user_id),
                "organization_id": str(organization_id),
                "form_data_id": str(form_data_id),
            },
        )
        if chat:
            return PatientChat_Db(**chat)
        return None

    @staticmethod
    async def count(
        user_id: PyObjectId,
        organization_id: PyObjectId,
    ) -> int:
        return await PatientChat.data_service.count(
            collection=PatientChat.DB_PATIENT_CHAT,
            query={
                "user_id": str(user_id),
                "organization_id": str(organization_id),
            },
        )

    @staticmethod
    async def get_chats(
        user_id: PyObjectId,
        organization_id: PyObjectId,
        skip: int = 0,
        limit: int = 1000,
    ) -> List[PatientChat_Db]:
        chats = await PatientChat.data_service.find_sorted_pagination(
            collection=PatientChat.DB_PATIENT_CHAT,
            query={
                "user_id": str(user_id),
                "organization_id": str(organization_id),
            },
            sort_key="updated_time",
            sort_direction=-1,
            skip=skip,
            limit=limit,
        )
        return [PatientChat_Db(**chat) for chat in chats]

    @staticmethod
    async def get_chat_by_id(
        chat_id: PyObjectId,
    ) -> Optional[PatientChat_Db]:
        chat = await PatientChat.data_service.find_one(
            collection=PatientChat.DB_PATIENT_CHAT,
            query={
                "_id": str(chat_id),
            },
        )
        if chat:
            return PatientChat_Db(**chat)
        return None

    @staticmethod
    async def update(
        chat_id: PyObjectId,
        patient_chat: PatientChat_Db,
    ):
        update_request = {"$set": {}}
        update_request["$set"]["chat"] = patient_chat.chat
        update_request["$set"]["updated_time"] = datetime.utcnow()
        return await PatientChat.data_service.update_one(
            collection=PatientChat.DB_PATIENT_CHAT,
            query={"_id": str(chat_id)},
            data=jsonable_encoder(update_request),
        )
