# -------------------------------------------------------------------------------
# Engineering
# etapestry_repositories.py
# -------------------------------------------------------------------------------
""" Service to manage eTapestry repositories """
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response, status

from app.api.authentication import get_current_user
from app.api.etapestry_data import add_etapestry_data
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.etapestry_repositories import (
    ETapestryRepositories,
    ETapestryRepository_Db,
    ETapestryRepositoryState,
    GetETapestryRepository_Out,
    GetMultipleETapestryRepository_Out,
    RegisterETapestryRepository_In,
    RegisterETapestryRepository_Out,
    UpdateETapestryRepository_In,
)
from app.utils.background_couroutines import AsyncTaskManager
from app.utils.elastic_search import ElasticsearchClient
from app.utils.etapestry import Etapestry
from app.utils.secrets import get_keyvault_secret, set_keyvault_secret

router = APIRouter(prefix="/api/etapestry-repositories", tags=["etapestry-repositories"])


@router.post(
    path="/",
    description="Add a new eTapestry repository",
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    operation_id="add_new_etapestry_repository",
)
async def add_new_etapestry_repository(
    etapestry_repository: RegisterETapestryRepository_In = Body(description="eTapestry repository information"),
    current_user: TokenData = Depends(get_current_user),
) -> RegisterETapestryRepository_Out:

    # Add the secret database name and API key to the keyvault
    database_name_id = PyObjectId()
    api_key_id = PyObjectId()
    await set_keyvault_secret(str(database_name_id), etapestry_repository.database_name)
    await set_keyvault_secret(str(api_key_id), etapestry_repository.api_key)

    # Add the eTapestry repository
    etapestry_repository_db = ETapestryRepository_Db(
        name=etapestry_repository.name,
        description=etapestry_repository.description,
        user_id=current_user.id,
        organization=current_user.organization,
        database_name_id=database_name_id,
        last_refresh_time=datetime.datetime.utcnow(),
        state=ETapestryRepositoryState.ACTIVE,
        api_key_id=api_key_id,
    )
    await ETapestryRepositories.create(etapestry_repository_db)

    # Create index in elasticsearch
    elastic_client = ElasticsearchClient()
    await elastic_client.create_index(index_name=str(etapestry_repository_db.id))

    # Pull accounts
    async_task_manager = AsyncTaskManager()
    async_task_manager.create_task(pull_accounts(etapestry_repository_db.id))

    return RegisterETapestryRepository_Out(_id=etapestry_repository_db.id)


@router.get(
    path="/",
    description="Get all the eTapestry respositories for the current user",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_all_etapestry_repositories",
)
async def get_all_etapestry_repositories(
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleETapestryRepository_Out:
    etapestry_repositories = await ETapestryRepositories.read(
        organization=current_user.organization, throw_on_not_found=False
    )

    return GetMultipleETapestryRepository_Out(
        repositories=[GetETapestryRepository_Out(**template.dict()) for template in etapestry_repositories]
    )


@router.get(
    path="/{etapestry_repository_id}",
    description="Get the eTapestry respository for the current user",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_etapestry_repository",
)
async def get_etapestry_repository(
    etapestry_repository_id: PyObjectId = Path(description="eTapestry repository id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetETapestryRepository_Out:
    etapestry_repository = await ETapestryRepositories.read(
        repository_id=etapestry_repository_id, organization=current_user.organization, throw_on_not_found=True
    )

    return GetETapestryRepository_Out(**etapestry_repository[0].dict())


@router.post(
    path="/{etapestry_repository_id}/refresh",
    description="Refresh the eTapestry respository for the current user",
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="refresh_etapestry_repository",
)
async def refresh_etapestry_repository(
    etapestry_repository_id: PyObjectId = Path(description="eTapestry repository id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Pull accounts only after one hour from the last refresh
    etapestry_repository = await ETapestryRepositories.read(
        repository_id=etapestry_repository_id, organization=current_user.organization, throw_on_not_found=True
    )
    if (datetime.datetime.utcnow() - etapestry_repository[0].last_refresh_time).seconds < 3600:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Too soon. Refresh is only allowed after 1 hour"
        )

    # Refresh the eTapestry respository
    await ETapestryRepositories.update(
        query_etapestry_repository_id=etapestry_repository_id,
        query_organization=current_user.organization,
        update_last_refresh_time=datetime.datetime.utcnow(),
    )

    async_task_manager = AsyncTaskManager()
    async_task_manager.create_task(pull_accounts(etapestry_repository_id))

    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.patch(
    path="/{etapestry_repository_id}",
    description="Update the eTapestry respository for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="update_etapestry_repository",
)
async def update_etapestry_repository(
    etapestry_repository_id: PyObjectId = Path(description="eTapestry repository id"),
    etapestry_repository: UpdateETapestryRepository_In = Body(description="eTapestry repository information"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Update the eTapestry respository
    await ETapestryRepositories.update(
        query_etapestry_repository_id=etapestry_repository_id,
        query_organization=current_user.organization,
        update_etapestry_repository_name=etapestry_repository.name,
        update_etapestry_repository_description=etapestry_repository.description,
        update_etapestry_repository_card_layout=etapestry_repository.card_layout,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    path="/{etapestry_repository_id}",
    description="Delete the eTapestry respository for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_etapestry_repository",
)
async def delete_etapestry_repository(
    etapestry_repository_id: PyObjectId = Path(description="eTapestry repository id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # Delete the eTapestry respository
    await ETapestryRepositories.update(
        query_etapestry_repository_id=etapestry_repository_id,
        query_organization=current_user.organization,
        update_etapestry_repository_state=ETapestryRepositoryState.DELETED,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def pull_accounts(repository_id: PyObjectId):
    print("pull_accounts", repository_id)

    repository = await ETapestryRepositories.read(repository_id=repository_id)
    repository = repository[0]

    api_key_id = repository.api_key_id
    databae_name_id = repository.database_name_id

    api_key = await get_keyvault_secret(str(api_key_id))
    if not api_key:
        raise Exception(f"API Key for {repository_id} not found")
    database_name = await get_keyvault_secret(str(databae_name_id))
    if not database_name:
        raise Exception(f"Database name for {repository_id} not found")

    etapestry = Etapestry(database_id=database_name, api_key=api_key)
    await etapestry.get_accounts(add_etapestry_data, repository_id=repository_id)
