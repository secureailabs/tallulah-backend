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
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class FormData_Base(SailBaseModel):
    form_template_id: PyObjectId = Field()
    values: Dict[StrictStr, Any] = Field(default=None)


class RegisterFormData_In(FormData_Base):
    pass


class FormDataState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class RegisterFormData_Out(SailBaseModel):
    id: PyObjectId = Field(alias="_id")


class FormData_Db(FormData_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetFormData_Out(FormData_Base):
    id: PyObjectId = Field(alias="_id")
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetMultipleFormData_Out(SailBaseModel):
    form_data: List[GetFormData_Out] = Field()


class FormDatas:
    DB_COLLECTION_FORM_DATA = "form_data"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        form_data: FormData_Db,
    ):
        return await FormDatas.data_service.insert_one(
            collection=FormDatas.DB_COLLECTION_FORM_DATA,
            data=jsonable_encoder(form_data),
        )

    @staticmethod
    async def read(
        form_data_id: Optional[PyObjectId] = None,
        form_template_id: Optional[PyObjectId] = None,
        throw_on_not_found: bool = True,
    ) -> List[FormData_Db]:
        form_data_list = []

        query = {}
        if form_data_id:
            query["_id"] = str(form_data_id)
        if form_template_id:
            query["form_template_id"] = str(form_template_id)

        # only read the non deleted ones
        query["state"] = FormDataState.ACTIVE.value

        response = await FormDatas.data_service.find_by_query(
            collection=FormDatas.DB_COLLECTION_FORM_DATA,
            query=jsonable_encoder(query),
        )

        if response:
            for form_data in response:
                form_data_list.append(FormData_Db(**form_data))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No messages found for query: {query}",
            )

        return form_data_list

    @staticmethod
    async def update(query_form_data_id: PyObjectId, form_data_state: Optional[FormDataState] = None):
        query = {}
        if query_form_data_id:
            query["_id"] = str(query_form_data_id)

        update_request = {"$set": {}}
        if form_data_state:
            update_request["$set"]["state"] = form_data_state.value

        update_response = await FormDatas.data_service.update_one(
            collection=FormDatas.DB_COLLECTION_FORM_DATA,
            query=query,
            data=jsonable_encoder(update_request),
        )
        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FormTemplate not found or no changes to update",
            )
