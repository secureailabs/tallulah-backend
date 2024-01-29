# -------------------------------------------------------------------------------
# Engineering
# form_data.py
# -------------------------------------------------------------------------------
""" Service to manage form datas """
# -------------------------------------------------------------------------------
# Copyright (C) 2023 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------


from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.form_data import (
    FormData_Db,
    FormDatas,
    FormDataState,
    GetFormData_Out,
    GetMultipleFormData_Out,
    RegisterFormData_In,
    RegisterFormData_Out,
)
from app.models.form_templates import FormMediaTypes, FormTemplates, GetStorageUrl_Out
from app.utils.azure_blob_manager import AzureBlobManager
from app.utils.elastic_search import ElasticsearchClient
from app.utils.secrets import secret_store

router = APIRouter(prefix="/api/form-data", tags=["form-data"])


@router.post(
    path="/",
    description="Add a new form data",
    status_code=status.HTTP_201_CREATED,
    operation_id="add_form_data",
)
async def add_form_data(
    form_data: RegisterFormData_In = Body(description="Form data information"),
) -> RegisterFormData_Out:
    form_data_db = FormData_Db(
        form_template_id=form_data.form_template_id,
        values=form_data.values,
    )
    await FormDatas.create(form_data_db)

    # Add the form data to elasticsearch for search
    elastic_client = ElasticsearchClient()
    await elastic_client.insert_document(
        index_name=str(form_data.form_template_id), id=str(form_data_db.id), document=form_data.values
    )

    return RegisterFormData_Out(_id=form_data_db.id)


@router.get(
    path="/",
    description="Get all the form data for the current user for the template",
    status_code=status.HTTP_200_OK,
    operation_id="get_all_form_data",
)
async def get_all_form_data(
    form_template_id: PyObjectId = Query(description="Form template id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleFormData_Out:
    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_template_id, organization=current_user.organization, throw_on_not_found=True
    )

    # TODO: Add pagination to this
    form_data_list = await FormDatas.read(form_template_id=form_template_id, throw_on_not_found=False)

    return GetMultipleFormData_Out(form_data=[GetFormData_Out(**form_data.dict()) for form_data in form_data_list])


@router.get(
    path="/upload",
    description="Get the upload url for the form data",
    status_code=status.HTTP_200_OK,
    operation_id="get_upload_url",
)
async def get_upload_url(
    media_type: FormMediaTypes = Query(description="Media type"),
) -> GetStorageUrl_Out:
    storage_manager = AzureBlobManager(
        secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "form-" + media_type.value.lower()
    )

    # Get the upload url
    media_id = PyObjectId()
    upload_url = storage_manager.generate_write_sas(str(media_id))

    return GetStorageUrl_Out(id=media_id, url=upload_url)


@router.get(
    path="/download",
    description="Get the download url for the form media",
    status_code=status.HTTP_200_OK,
    operation_id="get_download_url",
)
async def get_download_url(
    form_data_id: PyObjectId = Query(description="Form media id"),
    media_type: FormMediaTypes = Query(description="Media type"),
) -> GetStorageUrl_Out:
    storage_manager = AzureBlobManager(
        secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "form-" + media_type.value.lower()
    )

    # Get the download url
    download_url = storage_manager.generate_read_sas(str(form_data_id))

    return GetStorageUrl_Out(id=form_data_id, url=download_url)


@router.get(
    path="/search",
    description="Search the text form data for the current user for the template",
    status_code=status.HTTP_200_OK,
    operation_id="search_form_data",
)
async def search_form_data(
    form_template_id: PyObjectId = Query(description="Form template id"),
    search_query: str = Query(description="Search query"),
    current_user: TokenData = Depends(get_current_user),
):
    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_template_id, organization=current_user.organization, throw_on_not_found=True
    )

    # Search the form data
    elastic_client = ElasticsearchClient()
    response = await elastic_client.search(index_name=str(form_template_id), search_query=search_query)

    return response


@router.get(
    path="/{form_data_id}",
    description="Get the response data for the form",
    status_code=status.HTTP_200_OK,
    operation_id="get_form_data",
)
async def get_form_data(
    form_data_id: PyObjectId = Path(description="Form data id"),
    current_user: TokenData = Depends(get_current_user),
) -> GetFormData_Out:
    form_data = await FormDatas.read(form_data_id=form_data_id, throw_on_not_found=True)

    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_data[0].form_template_id, organization=current_user.organization, throw_on_not_found=True
    )

    return GetFormData_Out(**form_data[0].dict())


@router.delete(
    path="/{form_data_id}",
    description="Delete the response template for the current user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_form_data",
)
async def delete_form_data(
    form_data_id: PyObjectId = Path(description="Form data id"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    # TODO: Very bad approach to delete. Improve it. Maybe use aggregation to delete
    form_data = await FormDatas.read(form_data_id=form_data_id, throw_on_not_found=True)

    # Check if the user is the owner of the response template
    _ = await FormTemplates.read(
        template_id=form_data[0].form_template_id, organization=current_user.organization, throw_on_not_found=True
    )

    # Delete the response template
    await FormDatas.update(
        query_form_data_id=form_data_id,
        form_data_state=FormDataState.DELETED,
    )

    # Delete from the elastic search cluster as well
    elastic_client = ElasticsearchClient()
    await elastic_client.delete_document(index_name=str(form_data[0].form_template_id), id=str(form_data_id))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
