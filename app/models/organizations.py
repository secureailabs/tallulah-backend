# -------------------------------------------------------------------------------
# Engineering
# organizations.py
# -------------------------------------------------------------------------------
"""Models used by organizations service"""
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
from pydantic import EmailStr, Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class ExportState(Enum):
    REQUESTED = "REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExportType(Enum):
    CSV = "csv"
    JSON = "json"


class Organization_Base(SailBaseModel):
    name: StrictStr = Field()
    admin: EmailStr = Field()


class Organization_Db(Organization_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    account_creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetOrganizations_Out(Organization_Base):
    id: PyObjectId = Field()


class GetMultipleOrganizations_Out(SailBaseModel):
    organizations: List[GetOrganizations_Out]


class ExportData_Base(SailBaseModel):
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    export_type: ExportType = Field()
    status: ExportState = Field(default=ExportState.REQUESTED)
    request_time: datetime = Field(default_factory=datetime.utcnow)
    export_time: datetime = Field(default_factory=datetime.utcnow)
    filename: Optional[StrictStr] = Field(default=None)


class ExportData_Db(ExportData_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")


class ExportData_Out(ExportData_Base):
    id: PyObjectId = Field()


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
        throw_on_not_found: bool = True,
    ) -> List[Organization_Db]:
        organization_list = []

        query = {}
        if name:
            query["name"] = name
        if organization_id:
            query["_id"] = str(organization_id)

        response = await Organizations.data_service.find_by_query(
            collection=Organizations.DB_COLLECTION_ORGANIZATION,
            query=query,
        )

        if response:
            for organization in response:
                organization_list.append(Organization_Db(**organization))
        elif throw_on_not_found:
            raise HTTPException(status_code=404, detail="Organization not found")

        return organization_list


class DataExports:
    DB_COLLECTION_DATA_EXPORTS = "organization_data_exports"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        export: ExportData_Db,
    ):
        return await DataExports.data_service.insert_one(
            collection=DataExports.DB_COLLECTION_DATA_EXPORTS,
            data=jsonable_encoder(export),
        )

    @staticmethod
    async def update(
        export: ExportData_Db,
    ):
        update_request = {"$set": {}}
        update_request["$set"]["status"] = export.status
        update_request["$set"]["export_time"] = datetime.utcnow()
        update_request["$set"]["filename"] = export.filename
        return await DataExports.data_service.update_one(
            collection=DataExports.DB_COLLECTION_DATA_EXPORTS,
            query={"_id": str(export.id)},
            data=jsonable_encoder(update_request),
        )

    @staticmethod
    async def read(
        export_id: Optional[PyObjectId] = None,
        organization_id: Optional[PyObjectId] = None,
        throw_on_not_found: bool = True,
    ) -> List[ExportData_Db]:
        export_list = []

        query = {}
        if export_id:
            query["_id"] = str(export_id)
        if organization_id:
            query["organization_id"] = str(organization_id)

        response = await DataExports.data_service.find_by_query(
            collection=DataExports.DB_COLLECTION_DATA_EXPORTS,
            query=query,
        )

        exports = []
        if response:
            for export in response:
                exports.append(ExportData_Db(**export))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No messages found for query: {query}",
            )

        return exports
