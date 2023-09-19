# -------------------------------------------------------------------------------
# Engineering
# accounts.py
# -------------------------------------------------------------------------------
"""Models used by account management service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Secure Ai Labs, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Secure Ai Labs, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, Field, StrictStr

from app.data import operations as data_service
from app.models.common import BasicObjectInfo, PyObjectId, SailBaseModel


class UserRole(Enum):
    SAIL_ADMIN = "SAIL_ADMIN"
    USER = "USER"


class UserAccountState(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"


class User_Base(SailBaseModel):
    name: StrictStr = Field()
    email: EmailStr = Field()
    job_title: StrictStr = Field()
    roles: List[UserRole] = Field()
    avatar: Optional[StrictStr] = Field(default=None)


class User_Db(User_Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    account_creation_time: datetime = Field(default_factory=datetime.utcnow)
    hashed_password: StrictStr = Field()
    account_state: UserAccountState = Field()
    last_login_time: Optional[datetime] = Field(default=None)
    failed_login_attempts: int = Field(default=0)


class UserInfo_Out(User_Base):
    id: PyObjectId = Field(alias="_id")
    organization: BasicObjectInfo = Field()
    freemium: bool = Field(default=True)


class RegisterUser_In(User_Base):
    password: str = Field()


class RegisterUser_Out(SailBaseModel):
    id: PyObjectId = Field(alias="_id")


class GetUsers_Out(User_Base):
    id: PyObjectId = Field(alias="_id")
    name: StrictStr = Field()
    email: EmailStr = Field()
    job_title: StrictStr = Field()
    roles: List[UserRole] = Field()
    avatar: Optional[StrictStr] = Field()


class GetMultipleUsers_Out(SailBaseModel):
    users: List[GetUsers_Out] = Field()


class UpdateUser_In(SailBaseModel):
    job_title: Optional[StrictStr] = Field()
    roles: Optional[List[UserRole]] = Field()
    account_state: Optional[UserAccountState] = Field()
    avatar: Optional[StrictStr] = Field()


class Users:
    DB_COLLECTION_USERS = "users"

    @staticmethod
    async def create(
        user: User_Db,
    ):
        return await data_service.insert_one(
            collection=Users.DB_COLLECTION_USERS,
            data=jsonable_encoder(user),
        )

    @staticmethod
    async def read(
        user_id: Optional[PyObjectId] = None,
        email: Optional[str] = None,
        throw_on_not_found: bool = True,
    ) -> List[User_Db]:
        dataset_version_list = []

        query = {}
        if user_id:
            query["_id"] = user_id
        if email:
            query["email"] = email

        response = await data_service.find_by_query(
            collection=Users.DB_COLLECTION_USERS,
            query=jsonable_encoder(query),
        )

        if response:
            for data_model in response:
                dataset_version_list.append(User_Db(**data_model))
        elif throw_on_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found",
            )

        return dataset_version_list

    @staticmethod
    async def update(
        query_user_id: Optional[PyObjectId] = None,
        update_job_title: Optional[str] = None,
        update_avatar: Optional[str] = None,
        update_account_state: Optional[UserAccountState] = None,
        update_last_login_time: Optional[datetime] = None,
        update_failed_login_attempts: Optional[int] = None,
        increment_failed_login_attempts: Optional[bool] = None,
    ):
        query = {}
        if query_user_id:
            query["_id"] = str(query_user_id)

        update_request = {"$set": {}}
        if update_last_login_time:
            update_request["$set"]["state"] = update_last_login_time
        if update_job_title:
            update_request["$set"]["job_title"] = update_job_title
        if update_avatar:
            update_request["$set"]["avatar"] = update_avatar
        if update_account_state:
            update_request["$set"]["account_state"] = update_account_state.value
        if update_failed_login_attempts:
            update_request["$set"]["failed_login_attempts"] = update_failed_login_attempts
        if increment_failed_login_attempts:
            update_request["$inc"] = {"failed_login_attempts": 1}

        update_response = await data_service.update_many(
            collection=Users.DB_COLLECTION_USERS,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found or no changes to update",
            )
