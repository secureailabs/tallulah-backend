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

mongodb_host = get_secret("mongodb_host")
client = motor.motor_asyncio.AsyncIOMotorClient(f"{mongodb_host}:27017/")
sail_db = client["tallulah"]


async def find_one(collection, query) -> Optional[dict]:
    return await sail_db[collection].find_one(query)


async def find_all(collection: str) -> list:
    return await sail_db[collection].find().to_list(1000)


async def find_sorted(collection: str, query: Dict, sort_key: str, sort_direction: int) -> list:
    return await sail_db[collection].find(query).sort(sort_key, sort_direction).to_list(1000)


async def find_sorted_pagination(
    collection: str, query: Dict, sort_key: str, sort_direction: int, skip: int, limit: int
) -> list:
    return await sail_db[collection].find(query).sort(sort_key, sort_direction).skip(skip).limit(limit).to_list(1000)


async def find_by_query(collection: str, query) -> List[Dict[str, Any]]:
    return await sail_db[collection].find(query).to_list(1000)


async def insert_one(collection: str, data) -> results.InsertOneResult:
    return await sail_db[collection].insert_one(data)


async def update_one(collection: str, query: dict, data) -> results.UpdateResult:
    return await sail_db[collection].update_one(query, data)


async def update_many(collection: str, query: dict, data) -> results.UpdateResult:
    return await sail_db[collection].update_many(query, data)


async def delete(collection: str, query: dict) -> results.DeleteResult:
    return await sail_db[collection].delete_one(query)


async def drop():
    return await client.drop_database(sail_db)
