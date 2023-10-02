# -------------------------------------------------------------------------------
# Engineering
# cache.py
# -------------------------------------------------------------------------------
"""Get the BasicObject with id and name for an id"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from typing import Dict

from app.data import operations as data_service
from app.models.common import BasicObjectInfo, PyObjectId

GLOBAL_CACHE: Dict[PyObjectId, BasicObjectInfo] = {}

DB_COLLECTION_USERS = "users"


async def get_basic_object(id: PyObjectId, collection_name: str) -> BasicObjectInfo:
    if id in GLOBAL_CACHE:
        return GLOBAL_CACHE[id]
    else:
        # Get the user from the database
        object = await data_service.find_one(collection_name, {"_id": str(id)})
        if not object:
            raise Exception(f"{str(id)} in {collection_name} not found")
        basic_object = BasicObjectInfo(id=id, name=object["name"])
        # Add the user to the cache
        GLOBAL_CACHE[id] = basic_object
    return basic_object


async def get_basic_user(id: PyObjectId) -> BasicObjectInfo:
    return await get_basic_object(id, DB_COLLECTION_USERS)
