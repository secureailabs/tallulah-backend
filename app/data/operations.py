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

from typing import Any, Dict, List, Optional

import motor.motor_asyncio
import pymongo.results as results

from app.utils.secrets import get_secret


class DatabaseOperations:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseOperations, cls).__new__(cls)
            cls.mongodb_host = get_secret("mongodb_host")
            cls.client = motor.motor_asyncio.AsyncIOMotorClient(f"{cls.mongodb_host}:27017/")
            cls.sail_db = cls.client["tallulah"]
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
            .to_list(1000)
        )

    async def find_by_query(self, collection: str, query) -> List[Dict[str, Any]]:
        return await self.sail_db[collection].find(query).to_list(1000)

    async def insert_one(self, collection: str, data) -> results.InsertOneResult:
        return await self.sail_db[collection].insert_one(data)

    async def update_one(self, collection: str, query: dict, data) -> results.UpdateResult:
        return await self.sail_db[collection].update_one(query, data)

    async def update_many(self, collection: str, query: dict, data) -> results.UpdateResult:
        return await self.sail_db[collection].update_many(query, data)

    async def delete(self, collection: str, query: dict) -> results.DeleteResult:
        return await self.sail_db[collection].delete_one(query)

    async def drop(self):
        return await self.client.drop_database(self.sail_db)
