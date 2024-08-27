# -------------------------------------------------------------------------------
# Engineering
# common.py
# -------------------------------------------------------------------------------
"""Base Model Definitions for API Services"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, GetJsonSchemaHandler, StrictStr
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class PyObjectId(UUID):
    def __init__(self, value: Optional[str] = None, empty: bool = False):
        if empty:
            return super().__init__(str(UUID(int=0)))
        elif value is None:
            return super().__init__(str(uuid4()))
        else:
            return super().__init__(value)

    # @classmethod
    # def __get_validators__(cls):
    #     yield cls.validate

    @classmethod
    def validate(cls, v):
        _ = UUID(str(v), version=4)
        return UUID(str(v), version=4)

    # @classmethod
    # def __modify_schema__(cls, field_schema):
    #     field_schema.update(type="string")

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(UUID),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(cls.validate),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda x: str(x)),
        )


class SailBaseModel(BaseModel):
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class BasicObjectInfo(SailBaseModel):
    id: PyObjectId = Field(...)
    name: StrictStr = Field(...)


class KeyVaultObject(BaseModel):
    name: StrictStr = Field(...)
    version: StrictStr = Field(...)
