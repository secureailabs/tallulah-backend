# -------------------------------------------------------------------------------
# Engineering
# etapestry_data.py
# -------------------------------------------------------------------------------
""" Service to manage eTapestry data """
# -------------------------------------------------------------------------------
# Copyright (C) 2023 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

import traceback

from fastapi import APIRouter, Depends, Path, Query, Response, status
from fastapi.encoders import jsonable_encoder

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.etapestry_data import (
    ETapestryData_Db,
    ETapestryDatas,
    ETapestryDataState,
    GetETapestryData_Out,
    GetMultipleETapestryData_Out,
)
from app.models.etapestry_repositories import ETapestryRepositories
from app.utils.elastic_search import ElasticsearchClient
from app.utils.etapestry import AccountInfo

router = APIRouter(prefix="/api/etapestry-data", tags=["etapestry-data"])


@router.get(
    path="/",
    description="Get all the eTapestry data for the current user for the respository",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_all_etapestry_data",
)
async def get_all_etapestry_data(
    repository_id: PyObjectId = Query(description="Form template id"),
    skip: int = Query(default=0, description="Number of emails to skip"),
    limit: int = Query(default=200, description="Number of emails to return"),
    sort_key: str = Query(default="creation_time", description="Sort key"),
    sort_direction: int = Query(default=-1, description="Sort direction"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleETapestryData_Out:

    # Check if the user is the owner of the response template
    _ = await ETapestryRepositories.read(
        repository_id=repository_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    etapestry_data_list = await ETapestryDatas.read(
        repository_id=repository_id,
        skip=skip,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
        throw_on_not_found=False,
    )

    etapestry_data_count = await ETapestryDatas.count(repository_id=repository_id)

    return GetMultipleETapestryData_Out(
        etapestry_data=[GetETapestryData_Out(**etapestry_data.dict()) for etapestry_data in etapestry_data_list],
        count=etapestry_data_count,
        next=skip + limit,
        limit=limit,
    )


@router.get(
    path="/search",
    description="Search the text eTapestry data for the current user for the template",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="search_etapestry_data",
)
async def search_etapestry_data(
    repository_id: PyObjectId = Query(description="Form template id"),
    search_query: str = Query(description="Search query"),
    skip: int = Query(default=0, description="Number of etapestry data to skip"),
    limit: int = Query(default=10, description="Number of etapestry data to return"),
    current_user: TokenData = Depends(get_current_user),
):
    # Check if the user is the owner of the response template
    _ = await ETapestryRepositories.read(
        repository_id=repository_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    # Search the eTapestry data
    elastic_client = ElasticsearchClient()
    response = await elastic_client.search(
        index_name=str(repository_id), search_query=search_query, size=limit, skip=skip
    )

    return response


@router.get(
    path="/{etapestry_data_id}",
    description="Get the response data for the eTapestry",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_etapestry_data",
)
async def get_etapestry_data(
    etapestry_data_id: PyObjectId = Path(description="eTapestry data id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetETapestryData_Out:

    etapestry_data = await ETapestryDatas.read(data_id=etapestry_data_id, throw_on_not_found=True)

    # Check if the user is the owner of the response template
    _ = await ETapestryRepositories.read(
        repository_id=etapestry_data[0].repository_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )

    return GetETapestryData_Out(**etapestry_data[0].dict())


@router.patch(
    path="/{etapestry_data_id}",
    description="Update the tags and notes for the eTapestry data",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model_by_alias=False,
    operation_id="update_etapestry_data",
)
async def update_etapestry_data(
    etapestry_data_id: PyObjectId = Path(description="eTapestry data id"),
    tags: str = Query(default=None, description="Tags for the eTapestry data"),
    notes: str = Query(default=None, description="Notes for the eTapestry data"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    etapestry_data = await ETapestryDatas.read(data_id=etapestry_data_id, throw_on_not_found=True)

    # Check if the user is the owner of the response template
    _ = await ETapestryRepositories.read(
        repository_id=etapestry_data[0].repository_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )

    # Update the tags and notes
    await ETapestryDatas.update(
        query_id=etapestry_data_id,
        update_tags=tags.split(",") if tags else None,
        update_notes=notes,
    )

    # Update the data in the elastic search cluster as well
    elastic_client = ElasticsearchClient()
    await elastic_client.update_document(
        index_name=str(etapestry_data[0].repository_id),
        id=str(etapestry_data_id),
        document=jsonable_encoder(etapestry_data[0], exclude=set(["_id", "id"])),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    path="/{etapestry_data_id}",
    description="Delete the response template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_etapestry_data",
)
async def delete_etapestry_data(
    etapestry_data_id: PyObjectId = Path(description="eTapestry data id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # TODO: Bad approach to delete. Improve it. Maybe use aggregation to delete
    etapestry_data = await ETapestryDatas.read(data_id=etapestry_data_id, throw_on_not_found=True)

    # Check if the user is the owner of the response template
    _ = await ETapestryRepositories.read(
        repository_id=etapestry_data[0].repository_id,
        organization_id=current_user.organization_id,
        throw_on_not_found=True,
    )

    # Delete the response template
    await ETapestryDatas.update(
        query_id=etapestry_data_id,
        update_state=ETapestryDataState.DELETED,
    )

    # Delete from the elastic search cluster as well
    elastic_client = ElasticsearchClient()
    await elastic_client.delete_document(index_name=str(etapestry_data[0].repository_id), id=str(etapestry_data_id))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def add_etapestry_data(data: AccountInfo, repository_id: PyObjectId):
    try:
        # Add the eTapestry data
        etapestry_data_db = ETapestryData_Db(
            repository_id=repository_id,
            account=data,
            state=ETapestryDataState.ACTIVE,
        )
        inserted_data = await ETapestryDatas.create(etapestry_data_db)

        # Add the data to the elastic search cluster
        elastic_client = ElasticsearchClient()
        await elastic_client.insert_document(
            index_name=str(repository_id),
            id=str(inserted_data.id),
            document=jsonable_encoder(inserted_data, exclude=set(["_id", "id"])),
        )
    except Exception as e:
        print(f"Error adding eTapestry data: {e}")
        traceback.print_exc()
