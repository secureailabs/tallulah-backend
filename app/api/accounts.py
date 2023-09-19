# -------------------------------------------------------------------------------
# Engineering
# accounts.py
# -------------------------------------------------------------------------------
"""APIs to manage user accounts and organizations"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Secure Ai Labs, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Secure Ai Labs, Inc.
# -------------------------------------------------------------------------------


from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response, status

from app.api.authentication import get_current_user, get_password_hash
from app.models.accounts import (
    GetUsers_Out,
    RegisterUser_In,
    RegisterUser_Out,
    UpdateUser_In,
    User_Db,
    UserAccountState,
    UserRole,
    Users,
)
from app.models.authentication import TokenData
from app.models.common import BasicObjectInfo, PyObjectId

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    path="/",
    description="Add new user to organization",
    response_model=RegisterUser_Out,
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
    operation_id="register_user",
)
async def register_user(
    user: RegisterUser_In = Body(description="User details to register with the organization"),
) -> RegisterUser_Out:
    # Check if the user already exists
    user_db = await Users.read(email=user.email, throw_on_not_found=False)
    if user_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    # Also, don't allow the user to have a SAIL_ADMIN role
    if UserRole.SAIL_ADMIN in user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    # Create the user and add it to the database
    user_db = User_Db(
        name=user.name,
        email=user.email,
        roles=user.roles,
        job_title=user.job_title,
        hashed_password=get_password_hash(user.email, user.password),
        account_state=UserAccountState.ACTIVE,
    )
    await Users.create(user=user_db)

    return RegisterUser_Out(_id=user_db.id)


@router.get(
    path="/{user_id}",
    description="Get information about a user",
    response_model=GetUsers_Out,
    response_model_by_alias=False,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    operation_id="get_user",
)
async def get_user(
    user_id: PyObjectId = Path(description="UUID of the user"),
    current_user: TokenData = Depends(get_current_user),
) -> GetUsers_Out:
    # Check if the user exists
    user_db = await Users.read(user_id=user_id)

    return GetUsers_Out(**user_db[0].dict())


@router.patch(
    path="/{user_id}",
    description="""
        Update user information.
        """,
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="update_user_info",
)
async def update_user_info(
    user_id: PyObjectId = Path(description="UUID of the user"),
    update_user_info: UpdateUser_In = Body(description="User information to update"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    if user_id == current_user.id:
        pass
    elif UserRole.SAIL_ADMIN in current_user.roles:
        pass
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    # Other info can be updated by org admin, sail admin or the user itself
    await Users.update(
        query_user_id=user_id,
        update_job_title=update_user_info.job_title,
        update_avatar=update_user_info.avatar,
        update_account_state=update_user_info.account_state,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    path="/{user_id}",
    description="Soft Delete user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="soft_delete_user",
)
async def soft_delete_user(
    user_id: PyObjectId = Path(description="UUID of the user"),
    current_user: TokenData = Depends(get_current_user),
):
    # User must be admin of same organization or should be a SAIL Admin or same user
    if user_id == current_user.id or UserRole.SAIL_ADMIN in current_user.roles:
        pass
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    await Users.update(
        query_user_id=user_id,
        update_account_state=UserAccountState.INACTIVE,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
