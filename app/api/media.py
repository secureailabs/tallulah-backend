# -------------------------------------------------------------------------------
# Engineering
# media.py
# -------------------------------------------------------------------------------
""" Service to manage media uploads """
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status

from app.api.authentication import get_current_user
from app.models.authentication import TokenData
from app.models.common import PyObjectId
from app.models.form_templates import FormMediaTypes, GetStorageUrl_Out
from app.models.media import MediaMetadata, MediaMetadata_Db
from app.utils.azure_blob_manager import AzureBlobManager
from app.utils.secrets import secret_store

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get(
    path="/upload",
    description="Get the upload url for the media",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_media_upload_url",
)
async def get_media_upload_url(
    media_type: FormMediaTypes = Query(description="Media type"),
    current_user: TokenData = Depends(get_current_user),
) -> GetStorageUrl_Out:
    # Create a database entry for the media
    media_db = MediaMetadata_Db(organization_id=current_user.organization_id)
    await MediaMetadata.create(media_db)

    storage_manager = AzureBlobManager(
        secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "form-" + media_type.value.lower()
    )

    # Get the upload url
    upload_url = storage_manager.generate_write_sas(str(media_db.id))

    return GetStorageUrl_Out(id=media_db.id, url=upload_url)


@router.get(
    path="/download",
    description="Get the download url for the media",
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
    operation_id="get_media_download_url",
)
async def get_media_download_url(
    media_id: PyObjectId = Query(description="Form media id"),
    media_type: FormMediaTypes = Query(description="Media type"),
    current_user: TokenData = Depends(get_current_user),
) -> GetStorageUrl_Out:

    # Check if the media exists
    _ = await MediaMetadata.read(
        media_id=media_id, organization_id=current_user.organization_id, throw_on_not_found=True
    )

    storage_manager = AzureBlobManager(
        secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "form-" + media_type.value.lower()
    )

    # Get the download url
    download_url = storage_manager.generate_read_sas(str(media_id))

    return GetStorageUrl_Out(id=media_id, url=download_url)
