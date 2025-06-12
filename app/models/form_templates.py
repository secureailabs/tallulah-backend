# -------------------------------------------------------------------------------
# Engineering
# form_templates.py
# -------------------------------------------------------------------------------
"""Models used by response template management service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class FormFieldTypes(Enum):
    CHECKBOX = "CHECKBOX"
    CONSENT_CHECKBOX = "CONSENT_CHECKBOX"
    DATE = "DATE"
    DATETIME = "DATETIME"
    EMAIL = "EMAIL"
    FILE = "FILE"
    IMAGE = "IMAGE"
    NUMBER = "NUMBER"
    PHONE = "PHONE"
    PROFILE_PICTURE = "PROFILE_PICTURE"
    RADIO = "RADIO"
    SELECT = "SELECT"
    TEXT = "STRING"
    TEXTAREA = "TEXTAREA"
    TIME = "TIME"
    URL = "URL"
    VIDEO = "VIDEO"
    ZIPCODE = "ZIPCODE"


class FormMediaTypes(Enum):
    FILE = "FILE"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class FormTemplateState(Enum):
    TEMPLATE = "TEMPLATE"
    PUBLISHED = "PUBLISHED"
    DELETED = "DELETED"


class FormField(SailBaseModel):
    name: StrictStr = Field()
    label: StrictStr = Field()
    description: Optional[StrictStr] = Field(default=None)
    place_holder: StrictStr = Field(default=None)
    type: FormFieldTypes = Field(default=FormFieldTypes.TEXT)
    required: bool = Field(default=False)
    options: List[StrictStr] = Field(default=None)
    private: Optional[bool] = Field(default=False)


class FormFieldGroup(SailBaseModel):
    name: StrictStr = Field()
    description: Optional[StrictStr] = Field(default=None)
    fields: List[FormField] = Field(default=None)


class CardLayout(SailBaseModel):
    name: StrictStr = Field()
    fields: List[StrictStr] = Field(default=None)
    title_field: Optional[List[StrictStr]] = Field(default=None)


class FormTemplate_Base(SailBaseModel):
    name: StrictStr = Field()
    description: Optional[StrictStr] = Field(default=None)
    field_groups: List[FormFieldGroup] = Field(default=None)
    card_layout: Optional[CardLayout] = Field(default=None)
    logo: Optional[StrictStr] = Field(default=None)


class GetStorageUrl_Out(SailBaseModel):
    id: PyObjectId = Field()
    url: StrictStr = Field()


class RegisterFormTemplate_In(FormTemplate_Base):
    pass


class RegisterFormTemplate_Out(SailBaseModel):
    id: PyObjectId = Field()


class FormTemplate_Db(FormTemplate_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    state: FormTemplateState = Field(default=FormTemplateState.TEMPLATE)
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    last_edit_time: datetime = Field(default_factory=datetime.utcnow)
    email_subscription: Optional[List[PyObjectId]] = Field(default=[])


class GetFormTemplate_Out(FormTemplate_Base):
    id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    state: FormTemplateState = Field()
    last_edit_time: datetime = Field(default_factory=datetime.utcnow)
    email_subscription: Optional[List[PyObjectId]] = Field(default=[])


class GetMultipleFormTemplate_Out(SailBaseModel):
    templates: List[GetFormTemplate_Out] = Field()


class UpdateFormTemplate_In(SailBaseModel):
    name: Optional[StrictStr] = Field(default=None)
    description: Optional[StrictStr] = Field(default=None)
    field_groups: Optional[List[FormFieldGroup]] = Field(default=None)
    card_layout: Optional[CardLayout] = Field(default=None)
    logo: Optional[StrictStr] = Field(default=None)


class FormTheme(SailBaseModel):
    theme: StrictStr = Field()
    count: int = Field()


class FormTemplateData_Base(SailBaseModel):
    top_themes: Optional[List[FormTheme]] = Field(default=None)


class FormTemplateData_Db(FormTemplateData_Base):
    # Override with form_template_id
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    updation_time: datetime = Field(default_factory=datetime.utcnow)


class FormTemplates:
    DB_COLLECTION_FORM_TEMPLATES = "form_templates"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        form_template: FormTemplate_Db,
    ):
        return await FormTemplates.data_service.insert_one(
            collection=FormTemplates.DB_COLLECTION_FORM_TEMPLATES,
            data=jsonable_encoder(form_template),
        )

    @staticmethod
    async def read(
        organization_id: Optional[PyObjectId] = None,
        template_id: Optional[PyObjectId] = None,
        state: Optional[FormTemplateState] = None,
        throw_on_not_found: bool = True,
    ) -> List[FormTemplate_Db]:
        form_template_list = []

        query = {}
        if template_id:
            query["_id"] = str(template_id)
        if organization_id:
            query["organization_id"] = str(organization_id)
        if state:
            query["state"] = state.value
        else:
            query["state"] = {"$ne": FormTemplateState.DELETED.value}

        response = await FormTemplates.data_service.find_by_query(
            collection=FormTemplates.DB_COLLECTION_FORM_TEMPLATES,
            query=jsonable_encoder(query),
        )

        if response:
            for form_template in response:
                form_template_list.append(FormTemplate_Db(**form_template))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No messages found for query: {query}",
            )

        return form_template_list

    @staticmethod
    async def update(
        query_form_template_id: Optional[PyObjectId] = None,
        query_organization_id: Optional[PyObjectId] = None,
        update_form_template_name: Optional[StrictStr] = None,
        update_form_template_state: Optional[FormTemplateState] = None,
        update_form_template_description: Optional[StrictStr] = None,
        update_form_template_field_groups: Optional[List[FormFieldGroup]] = None,
        update_form_template_logo: Optional[StrictStr] = None,
        udpate_form_template_card_layout: Optional[CardLayout] = None,
        update_form_template_last_edit_time: Optional[datetime] = None,
        subscribing_user_id: Optional[PyObjectId] = None,
        unsubscribing_user_id: Optional[PyObjectId] = None,
    ):
        query = {}
        if query_form_template_id:
            query["_id"] = str(query_form_template_id)
        if query_organization_id:
            query["organization_id"] = str(query_organization_id)

        update_request = {"$set": {}}
        if update_form_template_name:
            update_request["$set"]["name"] = update_form_template_name
        if update_form_template_description:
            update_request["$set"]["description"] = update_form_template_description
        if update_form_template_field_groups:
            update_request["$set"]["field_groups"] = update_form_template_field_groups
        if update_form_template_last_edit_time:
            update_request["$set"]["last_edit_time"] = update_form_template_last_edit_time
        if update_form_template_state:
            update_request["$set"]["state"] = update_form_template_state.value
        # TODO: change everywhere how to perform a delete operation
        # in the following case, if the update involves deletion of logo, it has to be done by setting it to an empty string
        if update_form_template_logo is not None:
            update_request["$set"]["logo"] = update_form_template_logo
        if udpate_form_template_card_layout:
            update_request["$set"]["card_layout"] = udpate_form_template_card_layout
        if subscribing_user_id:
            update_request["$addToSet"] = {"email_subscription": subscribing_user_id}
        if unsubscribing_user_id:
            update_request["$pull"] = {"email_subscription": unsubscribing_user_id}

        update_response = await FormTemplates.data_service.update_many(
            collection=FormTemplates.DB_COLLECTION_FORM_TEMPLATES,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FormTemplate not found or no changes to update",
            )


class FormTemplatesData:
    DB_COLLECTION_FORM_TEMPLATES_DATA = "form_templates_data"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        form_template_data: FormTemplateData_Db,
    ):
        return await FormTemplatesData.data_service.insert_one(
            collection=FormTemplatesData.DB_COLLECTION_FORM_TEMPLATES_DATA,
            data=jsonable_encoder(form_template_data),
        )

    @staticmethod
    async def update(
        form_template_data: FormTemplateData_Db,
    ):
        update_request = {"$set": {}}
        update_request["$set"]["top_themes"] = form_template_data.top_themes
        update_request["$set"]["updation_time"] = datetime.utcnow()
        return await FormTemplatesData.data_service.update_one(
            collection=FormTemplatesData.DB_COLLECTION_FORM_TEMPLATES_DATA,
            query={"_id": str(form_template_data.id)},
            data=jsonable_encoder(update_request),
        )

    @staticmethod
    async def get_template_data(
        form_template_id: PyObjectId,
    ) -> Optional[FormTemplateData_Db]:
        template = await FormTemplatesData.data_service.find_one(
            collection=FormTemplatesData.DB_COLLECTION_FORM_TEMPLATES_DATA,
            query={
                "_id": str(form_template_id),
            },
        )
        if template:
            return FormTemplateData_Db(**template)
        return None
