# -------------------------------------------------------------------------------
# Engineering
# dashboard_templates.py
# -------------------------------------------------------------------------------
"""Models used by dashboard template management service"""
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
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class DashboardWidgetTypes(Enum):
    CHART = "CHART"
    TABLE = "TABLE"
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    PIE_CHART = "PIE_CHART"
    HISTOGRAM = "HISTOGRAM"
    BAR_CHART = "BAR_CHART"
    LINE_CHART = "LINE_CHART"
    SCATTER_PLOT = "SCATTER_PLOT"
    AREA_CHART = "AREA_CHART"
    BUBBLE_CHART = "BUBBLE_CHART"
    MAP = "MAP"
    INFOGRAPHIC = "INFOGRAPHIC"
    RADAR_CHART = "RADAR_CHART"
    GAUGE_CHART = "GAUGE_CHART"
    TREE_MAP = "TREE_MAP"
    HEAT_MAP = "HEAT_MAP"
    BOX_PLOT = "BOX_PLOT"
    WATERFALL_CHART = "WATERFALL_CHART"
    NETWORK_DIAGRAM = "NETWORK_DIAGRAM"
    SANKEY_DIAGRAM = "SANKEY_DIAGRAM"


class DashboardTemplateState(Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class DashboardWidget(SailBaseModel):
    name: StrictStr = Field()
    description: Optional[StrictStr] = Field(default=None)
    type: DashboardWidgetTypes = Field()
    data_query: Dict = Field()


class DashboardLayout(SailBaseModel):
    widgets: List[DashboardWidget] = Field(default=None)


class DashboardTemplate_Base(SailBaseModel):
    name: StrictStr = Field()
    description: Optional[StrictStr] = Field(default=None)
    repository_id: PyObjectId = Field()
    layout: DashboardLayout = Field(default=None)


class RegisterDashboardTemplate_In(DashboardTemplate_Base):
    pass


class RegisterDashboardTemplate_Out(SailBaseModel):
    id: PyObjectId = Field()


class DashboardTemplate_Db(DashboardTemplate_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    state: DashboardTemplateState = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class GetDashboardTemplate_Out(DashboardTemplate_Base):
    id: PyObjectId = Field()
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    state: DashboardTemplateState = Field()
    last_edit_time: datetime = Field(default_factory=datetime.utcnow)


class UpdateDashboardTemplate_In(SailBaseModel):
    name: Optional[StrictStr] = Field(default=None)
    description: Optional[StrictStr] = Field(default=None)
    layout: Optional[DashboardLayout] = Field(default=None)


class DashboardTemplates:
    DB_COLLECTION_DASHBOARD_TEMPLATES = "dashboard-templates"
    data_service = DatabaseOperations()

    @staticmethod
    async def create(dashboard_template: DashboardTemplate_Db):
        return await DashboardTemplates.data_service.insert_one(
            collection=DashboardTemplates.DB_COLLECTION_DASHBOARD_TEMPLATES,
            data=jsonable_encoder(dashboard_template),
        )

    @staticmethod
    async def read(
        organization_id: Optional[PyObjectId] = None,
        template_id: Optional[PyObjectId] = None,
        repository_id: Optional[PyObjectId] = None,
        throw_on_not_found: bool = True,
    ) -> List[DashboardTemplate_Db]:
        dashboard_template_list = []

        query = {}
        if template_id:
            query["_id"] = str(template_id)
        if organization_id:
            query["organization_id"] = str(organization_id)
        if repository_id:
            query["repository_id"] = str(repository_id)

        query["state"] = {"$ne": DashboardTemplateState.DELETED.value}

        response = await DashboardTemplates.data_service.find_by_query(
            collection=DashboardTemplates.DB_COLLECTION_DASHBOARD_TEMPLATES,
            query=jsonable_encoder(query),
        )

        if response:
            for dashboard_template in response:
                dashboard_template_list.append(DashboardTemplate_Db(**dashboard_template))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No dashboard templates found for query: {query}",
            )

        return dashboard_template_list

    @staticmethod
    async def update(
        query_dashboard_template_id: Optional[PyObjectId] = None,
        query_organization_id: Optional[PyObjectId] = None,
        update_dashboard_template_name: Optional[StrictStr] = None,
        update_dashboard_template_description: Optional[StrictStr] = None,
        update_dashboard_template_layout: Optional[DashboardLayout] = None,
        update_dashboard_template_state: Optional[DashboardTemplateState] = None,
    ):
        query = {}
        if query_dashboard_template_id:
            query["_id"] = str(query_dashboard_template_id)
        if query_organization_id:
            query["organization_id"] = str(query_organization_id)

        update_request = {"$set": {}}
        if update_dashboard_template_name:
            update_request["$set"]["name"] = update_dashboard_template_name
        if update_dashboard_template_description:
            update_request["$set"]["description"] = update_dashboard_template_description
        if update_dashboard_template_layout:
            update_request["$set"]["layout"] = jsonable_encoder(update_dashboard_template_layout)
        if update_dashboard_template_state:
            update_request["$set"]["state"] = update_dashboard_template_state.value

        update_response = await DashboardTemplates.data_service.update_many(
            collection=DashboardTemplates.DB_COLLECTION_DASHBOARD_TEMPLATES,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dashboard Template not found or no changes to update",
            )
