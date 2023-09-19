# -------------------------------------------------------------------------------
# Engineering
# internal_utils.py
# -------------------------------------------------------------------------------
"""SAIL internal util API functionses"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Secure Ai Labs, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Secure Ai Labs, Inc.
# -------------------------------------------------------------------------------

from fastapi import APIRouter, Response, status

from app.data import operations as data_service

router = APIRouter(tags=["internal"])


@router.delete(
    path="/database",
    description="Drop the database",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="drop_database",
)
async def drop_database():
    await data_service.drop()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
