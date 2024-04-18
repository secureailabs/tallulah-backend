# -------------------------------------------------------------------------------
# Engineering
# dashboard_templates.py
# -------------------------------------------------------------------------------
""" Service to manage dashboard templates """
# -------------------------------------------------------------------------------
# Copyright (C) 2023 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.dashboard_templates import (
    DashboardTemplate_Db,
    DashboardTemplates,
    DashboardTemplateState,
    GetDashboardTemplate_Out,
    RegisterDashboardTemplate_In,
    RegisterDashboardTemplate_Out,
    UpdateDashboardTemplate_In,
)
from app.utils.elastic_search import ElasticsearchClient

router = APIRouter(prefix="/api/dashboard-templates", tags=["dashboard-templates"])


@router.post(
    path="/",
    description="Add a new dashboard template",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="add_new_dashboard_template",
)
async def add_new_dashboard_template(
    dashboard_template: RegisterDashboardTemplate_In = Body(description="Dashboard template information"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterDashboardTemplate_Out:

    # Add the dashboard template to the database
    dashboard_template_db = DashboardTemplate_Db(
        name=dashboard_template.name,
        description=dashboard_template.description,
        layout=dashboard_template.layout,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        repository_id=dashboard_template.repository_id,
        state=DashboardTemplateState.ACTIVE,
    )
    await DashboardTemplates.create(dashboard_template_db)

    return RegisterDashboardTemplate_Out(id=dashboard_template_db.id)


@router.get(
    path="/{dashboard_template_id}",
    description="Get the dashboard template for the current user",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_dashboard_template",
)
async def get_dashboard_template(
    dashboard_template_id: PyObjectId = Path(description="Dashboard template id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetDashboardTemplate_Out:
    dashboard_template = await DashboardTemplates.read(
        template_id=dashboard_template_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    return GetDashboardTemplate_Out(**dashboard_template[0].dict())


@router.get(
    path="/",
    description="Get the dashboard templates for the current user",
    status_code=status.HTTP_200_OK,
    response_model=List[GetDashboardTemplate_Out],
    response_model_by_alias=False,
    operation_id="get_dashboard_templates",
)
async def get_dashboard_templates(
    respository_id: PyObjectId = Query(description="Repository id to filter the dashboard templates"),
    current_user: TokenData = Depends(get_current_user),
) -> List[GetDashboardTemplate_Out]:

    dashboard_templates = await DashboardTemplates.read(
        organization_id=current_user.organization_id, repository_id=respository_id
    )

    return [GetDashboardTemplate_Out(**dashboard_template.dict()) for dashboard_template in dashboard_templates]


@router.post(
    path="/execute",
    description="Execute the queries in the dashboard template",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="execute_dashboard_template",
)
async def execute_dashboard_template(
    dashboard_template_id: Optional[PyObjectId] = Query(default=None, description="Dashboard template id"),
    repository_id: Optional[PyObjectId] = Query(default=None, description="Repository id"),
    current_user: TokenData = Depends(get_current_user),
) -> dict:

    # Fetch the dashboard template
    dashboard_template = await DashboardTemplates.read(
        template_id=dashboard_template_id,
        repository_id=repository_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )
    dashboard_template = dashboard_template[0]

    # Execute the queries in the dashboard template
    response = {}
    for query in dashboard_template.layout.widgets:
        es_client = ElasticsearchClient()
        query_result = await es_client.run_aggregation_query(index_name=str(repository_id), query=query.data_query)
        response[query.name] = query_result["aggregations"]

    return response


@router.patch(
    path="/{dashboard_template_id}",
    description="Update the dashboard template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model_by_alias=False,
    operation_id="update_dashboard_template",
)
async def update_dashboard_template(
    dashboard_template_id: PyObjectId = Path(description="Dashboard template id"),
    dashboard_template: UpdateDashboardTemplate_In = Body(description="Dashboard template information"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Update the dashboard template
    await DashboardTemplates.update(
        query_dashboard_template_id=dashboard_template_id,
        query_organization_id=current_user.organization_id,
        update_dashboard_template_name=dashboard_template.name,
        update_dashboard_template_description=dashboard_template.description,
        update_dashboard_template_layout=dashboard_template.layout,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    path="/{dashboard_template_id}",
    description="Delete the dashboard template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_dashboard_template",
)
async def delete_dashboard_template(
    dashboard_template_id: PyObjectId = Path(description="Dashboard template id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Delete the dashboard template
    await DashboardTemplates.update(
        query_dashboard_template_id=dashboard_template_id,
        query_organization_id=current_user.organization_id,
        update_dashboard_template_state=DashboardTemplateState.DELETED,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
