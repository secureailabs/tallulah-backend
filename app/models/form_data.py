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

import math
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import pgeocode
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

import app.utils.log_manager as logger
from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class FormDataState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class VideoMetadata(SailBaseModel):
    video_id: PyObjectId = Field()
    transcript: str = Field()


class AudioMetadata(SailBaseModel):
    audio_id: PyObjectId = Field()
    transcript: str = Field()


class ImageMetadata(SailBaseModel):
    image_id: PyObjectId = Field()
    transcript: str = Field()


class StructuredData(SailBaseModel):
    name: Optional[str]
    age: Optional[int]
    location: Optional[str]
    diagnosis: Optional[str]
    events: List[str]
    date_of_Event: Optional[str]
    emotions_of_event: List[str]
    overall_theme_or_basic_concerns: List[str]


class FormDataMetadata(SailBaseModel):
    video_metadata: List[VideoMetadata] = Field(default=[])
    audio_metadata: List[AudioMetadata] = Field(default=[])
    image_metadata: List[ImageMetadata] = Field(default=[])
    structured_data: Union[None, StructuredData, Dict[StrictStr, Any]] = Field(default=None)
    creation_time: datetime = Field(default=datetime.utcnow())


class FormData_Base(SailBaseModel):
    form_template_id: PyObjectId = Field()
    values: Dict[StrictStr, Any] = Field(default=None)


class RegisterFormData_In(FormData_Base):
    creation_time: Optional[datetime] = Field(default=None)


class RegisterFormData_Out(SailBaseModel):
    id: PyObjectId = Field()


class FormData_Db(FormData_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    chat_time: Optional[datetime] = Field(default=datetime.utcnow())
    state: FormDataState = Field(default=FormDataState.ACTIVE)
    themes: Optional[List[StrictStr]] = Field(default=None)
    metadata: Optional[FormDataMetadata] = Field(default=None)
    creation_time: datetime = Field(default=datetime.utcnow())


class GetFormData_Out(FormData_Base):
    id: PyObjectId = Field()
    state: FormDataState = Field(default=FormDataState.ACTIVE)
    themes: Optional[List[StrictStr]] = Field(default=None)
    metadata: Optional[FormDataMetadata] = Field(default=None)
    creation_time: datetime = Field()


class UpdateFormData_In(SailBaseModel):
    values: Dict[StrictStr, Any] = Field()


class GetMultipleFormData_Out(SailBaseModel):
    form_data: List[GetFormData_Out] = Field()
    count: int = Field()
    next: int = Field()
    limit: int = Field()


class FormFilter_In(SailBaseModel):
    kv: Optional[Dict[StrictStr, List[StrictStr]]] = Field(default=None)
    values_present: Optional[List[StrictStr]] = Field(default=None)
    values_not_present: Optional[List[StrictStr]] = Field(default=None)


class Location(SailBaseModel):
    latitude: float = Field()
    longitude: float = Field()
    city: str = Field()


class FormDataLocation(SailBaseModel):
    form_data_id: PyObjectId = Field()
    zipcode: str = Field()
    location: Location = Field()


class GetFormDataLocation_Out(SailBaseModel):
    form_data_location: List[FormDataLocation] = Field()


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
    def convert_form_data_to_string(form_data: FormData_Db):
        remove_form_fields = ["consentToTag", "image", "consent", "tags"]
        data = form_data.values

        # Remove unwanted fields
        for field in remove_form_fields:
            data.pop(field, None)

        patient = ""
        for key, value in data.items():
            if (
                "value" in value
                and isinstance(value["value"], str)
                and value["value"].strip()
                and value["value"].strip() != "n/a"
            ):
                patient += f"{value['label'] if 'label' in value else key}: {value['value'].strip()}, "

        return patient

    @staticmethod
    async def read_forms_without_tags() -> List[FormData_Db]:
        form_data_list = []
        query = {
            "values.tags": {"$exists": False}
            # "themes": {"$exists": False} # For missing themes only
        }
        response = await FormDatas.data_service.find_by_query(
            collection=FormDatas.DB_COLLECTION_FORM_DATA,
            query=jsonable_encoder(query),
        )
        if response:
            for form_data in response:
                form_data_list.append(FormData_Db(**form_data))

        return form_data_list

    @staticmethod
    async def read(
        form_data_id: Optional[PyObjectId] = None,
        form_template_id: Optional[PyObjectId] = None,
        data_filter: Optional[FormFilter_In] = None,
        field_not_exists: Optional[StrictStr] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort_key: str = "creation_time",
        sort_direction: int = -1,
        throw_on_not_found: bool = True,
    ) -> List[FormData_Db]:
        form_data_list = []

        query = {}
        if form_data_id:
            query["_id"] = str(form_data_id)
        if form_template_id:
            query["form_template_id"] = str(form_template_id)
        if data_filter:
            if data_filter.kv:
                for key, value in data_filter.kv.items():
                    query[f"values.{key}.value"] = {"$in": value}
            if data_filter.values_present:
                for field in data_filter.values_present:
                    query["$and"] = [
                        {f"values.{field}.value": {"$exists": True}},
                        {f"values.{field}.value": {"$ne": None}},
                        {f"values.{field}.value": {"$ne": ""}},
                        {f"values.{field}.value": {"$ne": []}},
                    ]
            if data_filter.values_not_present:
                for field in data_filter.values_not_present:
                    query["$or"] = [
                        {f"values.{field}.value": {"$exists": False}},
                        {f"values.{field}.value": None},
                        {f"values.{field}.value": {"$eq": []}},
                        {f"values.{field}.value": {"$eq": ""}},
                    ]

        if field_not_exists:
            query["$or"] = [{field_not_exists: {"$exists": False}}, {field_not_exists: None}]

        # only read the non deleted ones
        query["state"] = FormDataState.ACTIVE.value

        if skip is None and limit is None:
            response = await FormDatas.data_service.find_by_query(
                collection=FormDatas.DB_COLLECTION_FORM_DATA,
                query=jsonable_encoder(query),
            )
        elif skip is not None and limit is not None:
            response = await FormDatas.data_service.find_sorted_pagination(
                collection=FormDatas.DB_COLLECTION_FORM_DATA,
                query=jsonable_encoder(query),
                sort_key=sort_key,
                sort_direction=sort_direction,
                skip=skip,
                limit=limit,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both skip and limit need to be provided for pagination",
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
    async def count(
        form_template_id: Optional[PyObjectId] = None,
        data_filter: Optional[FormFilter_In] = None,
    ) -> int:
        query = {}
        if form_template_id:
            query["form_template_id"] = str(form_template_id)
        if data_filter:
            if data_filter.kv:
                for key, value in data_filter.kv.items():
                    query[f"values.{key}.value"] = {"$in": value}
            if data_filter.values_present:
                for field in data_filter.values_present:
                    query["$and"] = [
                        {f"values.{field}.value": {"$exists": True}},
                        {f"values.{field}.value": {"$ne": None}},
                        {f"values.{field}.value": {"$ne": ""}},
                        {f"values.{field}.value": {"$ne": []}},
                    ]
            if data_filter.values_not_present:
                for field in data_filter.values_not_present:
                    query["$or"] = [
                        {f"values.{field}.value": {"$exists": False}},
                        {f"values.{field}.value": None},
                        {f"values.{field}.value": {"$eq": []}},
                        {f"values.{field}.value": {"$eq": ""}},
                    ]

        return await FormDatas.data_service.count(collection=FormDatas.DB_COLLECTION_FORM_DATA, query=query)

    @staticmethod
    async def update(
        query_form_data_id: PyObjectId,
        update_form_data_state: Optional[FormDataState] = None,
        update_form_data_values: Optional[Dict[StrictStr, Any]] = None,
        update_form_data_tags: Optional[List[StrictStr]] = None,
        update_form_data_themes: Optional[List[StrictStr]] = None,
        update_chat_time: Optional[datetime] = None,
        update_form_data_metadata: Optional[FormDataMetadata] = None,
        throw_on_no_update: bool = True,
    ):
        query = {}
        if query_form_data_id:
            query["_id"] = str(query_form_data_id)

        update_request = {"$set": {}}
        if update_form_data_state:
            update_request["$set"]["state"] = update_form_data_state.value
        if update_form_data_values:
            update_request["$set"]["values"] = update_form_data_values
        if update_form_data_tags:
            update_request["$set"]["values.tags"] = {
                "value": ", ".join(update_form_data_tags),
                "label": "Tags",
                "type": "STRING",
            }
        if update_form_data_themes:
            update_request["$set"]["themes"] = update_form_data_themes
        if update_chat_time:
            update_request["$set"]["chat_time"] = update_chat_time
        if update_form_data_metadata:
            update_request["$set"]["metadata"] = jsonable_encoder(update_form_data_metadata)

        update_response = await FormDatas.data_service.update_one(
            collection=FormDatas.DB_COLLECTION_FORM_DATA,
            query=query,
            data=jsonable_encoder(update_request),
        )
        if update_response.modified_count == 0:
            if throw_on_no_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Form Data not found or no changes to update",
                )

    @staticmethod
    async def aggregate_zipcodes(
        form_template_id: PyObjectId,
    ) -> List[FormDataLocation]:

        agg_pipeline = [
            {"$match": {"form_template_id": str(form_template_id), "state": FormDataState.ACTIVE.value}},
            {
                "$project": {
                    "_id": 1,
                    "zipcode": {
                        "$filter": {
                            "input": {"$objectToArray": "$values"},
                            "as": "item",
                            "cond": {"$eq": ["$$item.v.type", "ZIPCODE"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "zipcode": {"$first": "$zipcode.v.value"}}},
        ]

        response = await FormDatas.data_service.aggregate(
            collection=FormDatas.DB_COLLECTION_FORM_DATA,
            pipeline=agg_pipeline,
        )

        nomi = pgeocode.Nominatim("us")

        form_data_location_list: List[FormDataLocation] = []
        for zipcode in response:
            if "zipcode" not in zipcode or not zipcode["zipcode"]:
                continue

            zipcode_info = nomi.query_postal_code(zipcode["zipcode"])

            # check if latitude and longitude are valid
            if not zipcode_info["latitude"] or not zipcode_info["longitude"]:
                continue

            if math.isnan(zipcode_info["latitude"]) or math.isnan(zipcode_info["longitude"]):  # type: ignore
                logger.INFO({"message": f"Invalid latitude or longitude for zipcode: {zipcode['zipcode']}"})
                continue

            location = Location(
                latitude=zipcode_info["latitude"],  # type: ignore
                longitude=zipcode_info["longitude"],  # type: ignore
                city=zipcode_info["place_name"] + " " + zipcode_info["state_name"] + " " + zipcode_info["country_code"],  # type: ignore
            )
            form_data_location_list.append(
                FormDataLocation(form_data_id=zipcode["_id"], zipcode=zipcode["zipcode"], location=location)
            )

        return form_data_location_list
