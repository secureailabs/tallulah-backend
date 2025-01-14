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
from typing import Union

from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed


class SecretStore(BaseModel):
    AZURE_KEYVAULT_URL: str
    DEVOPS_KEYVAULT_URL: str
    JWT_SECRET: str
    MONGO_CONNECTION_URL: str
    MONGO_DB_NAME: str
    OUTLOOK_CLIENT_ID: str
    OUTLOOK_CLIENT_SECRET: str
    OUTLOOK_REDIRECT_URI: str
    EMAIL_NO_REPLY_REFRESH_TOKEN: str
    PASSWORD_PEPPER: str
    RABBIT_MQ_HOST: str
    RABBIT_MQ_QUEUE_NAME: str
    REDIS_PASSWORD: str
    REFRESH_SECRET: str
    SLACK_WEBHOOK: str
    TALLULAH_ADMIN_PASSWORD: str
    STORAGE_ACCOUNT_CONNECTION_STRING: str
    ELASTIC_HOST: str
    ELASTIC_PASSWORD: str
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    FIREBASE_CREDENTIALS: str
    FIREBASE_CREDENTIALS_FILE: str
    GOOGLE_RECAPTCHA_SECRET_KEY: str
    AZURE_COMM_CONNECTION_STRING: str
    AZURE_EMAIL_FROM_ADDRESS: str
    REDDIT_API_KEY: str
    REDDIT_API_SECRET: str
    MONGO_DB_CHARTS_PRIVATE_KEY: str

    class Config:
        frozen = True


def get_secret_env(secret_name) -> str:
    # Get the secrets from the environment variables
    if secret_name not in os.environ:
        raise KeyError(f"Secret {secret_name} not found in environment variables")
    return os.environ[secret_name]


secret_store = SecretStore(
    AZURE_KEYVAULT_URL=get_secret_env("AZURE_KEYVAULT_URL"),
    DEVOPS_KEYVAULT_URL=get_secret_env("DEVOPS_KEYVAULT_URL"),
    JWT_SECRET=get_secret_env("JWT_SECRET"),
    MONGO_CONNECTION_URL=get_secret_env("MONGO_CONNECTION_URL"),
    MONGO_DB_NAME=get_secret_env("MONGO_DB_NAME"),
    OUTLOOK_CLIENT_ID=get_secret_env("OUTLOOK_CLIENT_ID"),
    OUTLOOK_CLIENT_SECRET=get_secret_env("OUTLOOK_CLIENT_SECRET"),
    OUTLOOK_REDIRECT_URI=get_secret_env("OUTLOOK_REDIRECT_URI"),
    EMAIL_NO_REPLY_REFRESH_TOKEN=get_secret_env("EMAIL_NO_REPLY_REFRESH_TOKEN"),
    PASSWORD_PEPPER=get_secret_env("PASSWORD_PEPPER"),
    RABBIT_MQ_HOST=get_secret_env("RABBIT_MQ_HOST"),
    RABBIT_MQ_QUEUE_NAME=get_secret_env("RABBIT_MQ_QUEUE_NAME"),
    REDIS_PASSWORD=get_secret_env("REDIS_PASSWORD"),
    REFRESH_SECRET=get_secret_env("REFRESH_SECRET"),
    SLACK_WEBHOOK=get_secret_env("SLACK_WEBHOOK"),
    TALLULAH_ADMIN_PASSWORD=get_secret_env("TALLULAH_ADMIN_PASSWORD"),
    STORAGE_ACCOUNT_CONNECTION_STRING=get_secret_env("STORAGE_ACCOUNT_CONNECTION_STRING"),
    ELASTIC_HOST=get_secret_env("ELASTIC_HOST"),
    ELASTIC_PASSWORD=get_secret_env("ELASTIC_PASSWORD"),
    OPENAI_API_BASE=get_secret_env("OPENAI_API_BASE"),
    OPENAI_API_KEY=get_secret_env("OPENAI_API_KEY"),
    FIREBASE_CREDENTIALS=get_secret_env("FIREBASE_CREDENTIALS"),
    FIREBASE_CREDENTIALS_FILE=get_secret_env("FIREBASE_CREDENTIALS_FILE"),
    GOOGLE_RECAPTCHA_SECRET_KEY=get_secret_env("GOOGLE_RECAPTCHA_SECRET_KEY"),
    AZURE_COMM_CONNECTION_STRING=get_secret_env("AZURE_COMM_CONNECTION_STRING"),
    AZURE_EMAIL_FROM_ADDRESS=get_secret_env("AZURE_EMAIL_FROM_ADDRESS"),
    REDDIT_API_KEY=get_secret_env("REDDIT_API_KEY"),
    REDDIT_API_SECRET=get_secret_env("REDDIT_API_SECRET"),
    MONGO_DB_CHARTS_PRIVATE_KEY=get_secret_env("MONGO_DB_CHARTS_PRIVATE_KEY"),
)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def get_keyvault_secret(secret_name: str) -> Union[str, None]:
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=secret_store.AZURE_KEYVAULT_URL, credential=credential)  # type: ignore

    async with credential:
        async with secret_client:
            secret = await secret_client.get_secret(secret_name)
            return secret.value


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def set_keyvault_secret(secret_name: str, secret_value: str) -> None:
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=secret_store.AZURE_KEYVAULT_URL, credential=credential)  # type: ignore

    async with credential:
        async with secret_client:
            await secret_client.set_secret(secret_name, secret_value)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def delete_keyvault_secret(secret_name: str) -> None:
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=secret_store.AZURE_KEYVAULT_URL, credential=credential)  # type: ignore

    async with credential:
        async with secret_client:
            await secret_client.delete_secret(secret_name)
