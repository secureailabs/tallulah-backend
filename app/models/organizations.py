# -------------------------------------------------------------------------------
# Engineering
# organizations.py
# -------------------------------------------------------------------------------
"""Models used by account management service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime
from typing import Optional

from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class Organization_Base(SailBaseModel):
    name: StrictStr = Field()
    admin: EmailStr = Field()


class Organization_Db(Organization_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    account_creation_time: datetime = Field(default_factory=datetime.utcnow)


class Organizations:
    DB_COLLECTION_ORGANIZATION = "organizations"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        organization: Organization_Db,
    ):
        return await Organizations.data_service.insert_one(
            collection=Organizations.DB_COLLECTION_ORGANIZATION,
            data=jsonable_encoder(organization),
        )

    @staticmethod
    async def read(
        organization_id: Optional[PyObjectId] = None,
        name: Optional[StrictStr] = None,
    ):
        query = {}
        if name:
            query["name"] = name
        if organization_id:
            query["_id"] = str(organization_id)

        return await Organizations.data_service.find_one(
            collection=Organizations.DB_COLLECTION_ORGANIZATION,
            query=query,
        )
