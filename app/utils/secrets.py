# -------------------------------------------------------------------------------
# Engineering
# secrets.py
# -------------------------------------------------------------------------------
"""Get secrets"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

import os
from typing import Dict, Union

from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient
from tenacity import retry, stop_after_attempt, wait_fixed

initialization_vector: Dict[str, str] = {}


def get_secret(secret_name: str) -> str:
    global initialization_vector

    if secret_name not in initialization_vector:
        # read from environment variable
        if secret_name in os.environ:
            initialization_vector[secret_name] = os.environ[secret_name]
        else:
            raise Exception(f"Secret {secret_name} not found")

    return initialization_vector[secret_name]


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def get_keyvault_secret(secret_name: str) -> Union[str, None]:
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=get_secret("AZURE_KEYVAULT_URL"), credential=credential)  # type: ignore

    async with credential:
        async with secret_client:
            secret = await secret_client.get_secret(secret_name)
            return secret.value


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def set_keyvault_secret(secret_name: str, secret_value: str) -> None:
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=get_secret("AZURE_KEYVAULT_URL"), credential=credential)  # type: ignore

    async with credential:
        async with secret_client:
            await secret_client.set_secret(secret_name, secret_value)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def delete_keyvault_secret(secret_name: str) -> None:
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=get_secret("AZURE_KEYVAULT_URL"), credential=credential)  # type: ignore

    async with credential:
        async with secret_client:
            await secret_client.delete_secret(secret_name)
