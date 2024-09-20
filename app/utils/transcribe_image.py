# -------------------------------------------------------------------------------
# Engineering
# transcribe_image.py
# -------------------------------------------------------------------------------
""" Service to transcribe image files """
# -------------------------------------------------------------------------------
# Copyright (C) 2024 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from app.utils.azure_blob_manager import AzureBlobManager
from app.utils.azure_openai import OpenAiGenerator
from app.utils.secrets import secret_store


async def describe_image_from_id(image_id) -> str:
    storage_manager = AzureBlobManager(secret_store.STORAGE_ACCOUNT_CONNECTION_STRING, "form-image")
    image_file_url = storage_manager.generate_read_sas(file_name=str(image_id), expiry_hours=1)

    openai_generator = OpenAiGenerator(api_base=secret_store.OPENAI_API_BASE, api_key=secret_store.OPENAI_API_KEY)
    image_description = await openai_generator.describe_image(image_url=image_file_url)

    return image_description
