# -------------------------------------------------------------------------------
# Engineering
# operations.py
# -------------------------------------------------------------------------------
"""Async operations for the database"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

import asyncio
import os
from typing import Any, Dict, List, Optional, Tuple

import pymongo.results as results
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from motor import motor_asyncio
from motor.motor_asyncio import AsyncIOMotorChangeStream
from pymongo import ReturnDocument
from pymongo.server_api import ServerApi

from app.utils.secrets import secret_store


class DatabaseOperations:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            use_cert = True
            # write the certificate to a tmp file
            try:
                with open("/tmp/mongo_atlas_cert.pem", "w") as f:
                    credential = DefaultAzureCredential()
                    client = SecretClient(vault_url=secret_store.DEVOPS_KEYVAULT_URL, credential=credential)
                    secret = client.get_secret("mongo-connection-certificate")
                    if not secret.value:
                        raise Exception("Could not retrieve the secret")
                    f.write(secret.value)
            except:
                use_cert = False

            cls._instance = super(DatabaseOperations, cls).__new__(cls)
            cls.mongodb_host = secret_store.MONGO_CONNECTION_URL
            if use_cert:
                cls.client = motor_asyncio.AsyncIOMotorClient(
                    cls.mongodb_host,
                    tls=True,
                    tlsCertificateKeyFile="/tmp/mongo_atlas_cert.pem",
                    server_api=ServerApi("1"),
                    io_loop=asyncio.get_event_loop(),
                )
            else:
                cls.client = cls.client = motor_asyncio.AsyncIOMotorClient(
                    cls.mongodb_host,
                    io_loop=asyncio.get_event_loop(),
                )
            cls.sail_db = cls.client[secret_store.MONGO_DB_NAME]

            # remove the certificate
            os.remove("/tmp/mongo_atlas_cert.pem")
        return cls._instance

    async def find_one(self, collection, query) -> Optional[dict]:
        return await self.sail_db[collection].find_one(query)

    async def find_all(self, collection: str) -> list:
        return await self.sail_db[collection].find().to_list(1000)

    async def find_sorted(self, collection: str, query: Dict, sort_key: str, sort_direction: int) -> list:
        return await self.sail_db[collection].find(query).sort(sort_key, sort_direction).to_list(1000)

    async def find_sorted_pagination(
        self, collection: str, query: Dict, sort_key: str, sort_direction: int, skip: int, limit: int
    ) -> list:
        return (
            await self.sail_db[collection]
            .find(query)
            .sort(sort_key, sort_direction)
            .skip(skip)
            .limit(limit)
            .to_list(limit)
        )

    async def find_one_and_update(self, collection: str, query: Dict, update: Dict) -> Optional[dict]:
        return await self.sail_db[collection].find_one_and_update(
            query,
            update,
            upsert=False,
            return_document=ReturnDocument.AFTER,
        )

    async def find_by_query(self, collection: str, query) -> List[Dict[str, Any]]:
        return await self.sail_db[collection].find(query).to_list(1000)

    async def count(self, collection: str, query: Dict) -> int:
        return await self.sail_db[collection].count_documents(query)

    async def insert_one(self, collection: str, data) -> results.InsertOneResult:
        return await self.sail_db[collection].insert_one(data)

    async def update_one(self, collection: str, query: dict, data) -> results.UpdateResult:
        return await self.sail_db[collection].update_one(query, data)

    async def update_many(self, collection: str, query: dict, data) -> results.UpdateResult:
        return await self.sail_db[collection].update_many(query, data)

    async def delete(self, collection: str, query: dict) -> results.DeleteResult:
        return await self.sail_db[collection].delete_one(query)

    async def delete_many(self, collection: str, query: dict) -> results.DeleteResult:
        return await self.sail_db[collection].delete_many(query)

    async def drop(self):
        return await self.client.drop_database(self.sail_db)

    async def create_index(self, collection: str, index: List[Tuple[str, int]], unique: bool = False):
        return await self.sail_db[collection].create_index(index, unique=unique)

    async def aggregate(self, collection: str, pipeline: List[Dict]) -> List[Dict]:
        return await self.sail_db[collection].aggregate(pipeline).to_list(10000)

    async def get_change_stream(
        self, collection_name: str, pipeline: List[dict], resume_token: Optional[Any] = None
    ) -> AsyncIOMotorChangeStream:
        collection = self.sail_db[collection_name]
        if resume_token:
            change_stream = collection.watch(pipeline, resume_after=resume_token)
        else:
            change_stream = collection.watch(pipeline)
        return change_stream

    async def get_collection(self, collection_name: str):
        return self.sail_db[collection_name]
