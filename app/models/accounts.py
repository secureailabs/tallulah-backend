# -------------------------------------------------------------------------------
# Engineering
# accounts.py
# -------------------------------------------------------------------------------
"""Models used by account management service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, Field, StrictStr

from app.data.operations import DatabaseOperations
from app.models.common import PyObjectId, SailBaseModel


class UserRole(Enum):
    USER = "USER"
    TALLULAH_ADMIN = "TALLULAH_ADMIN"
    FORM_INTAKE_USER = "FORM_INTAKE_USER"
    EMAIL_INTEGRATION_USER = "EMAIL_INTEGRATION_USER"
    CONTENT_GENERATION_USER = "CONTENT_GENERATION_USER"
    PATIENT_PROFILE_USER = "PATIENT_PROFILE_USER"
    ETAPESTRY_USER = "ETAPESTRY_USER"


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
    organization_id: PyObjectId = Field()
    account_creation_time: datetime = Field(default_factory=datetime.utcnow)
    hashed_password: StrictStr = Field()
    state: UserAccountState = Field()
    last_login_time: Optional[datetime] = Field(default=None)
    failed_login_attempts: int = Field(default=0)


class UserInfo_Out(User_Base):
    id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    organization_name: StrictStr = Field()


class RegisterUser_In(User_Base):
    password: str = Field()
    organization_id: Optional[PyObjectId] = Field()
    organization_name: Optional[StrictStr] = Field()


class RegisterUser_Out(SailBaseModel):
    id: PyObjectId = Field()


class GetUsers_Out(User_Base):
    id: PyObjectId = Field()
    name: StrictStr = Field()
    organization_id: PyObjectId = Field()
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
    data_service = DatabaseOperations()

    @staticmethod
    async def create(
        user: User_Db,
    ):
        return await Users.data_service.insert_one(
            collection=Users.DB_COLLECTION_USERS,
            data=jsonable_encoder(user),
        )

    @staticmethod
    async def read(
        user_id: Optional[PyObjectId] = None,
        email: Optional[str] = None,
        user_role: Optional[UserRole] = None,
        throw_on_not_found: bool = True,
    ) -> List[User_Db]:
        dataset_version_list = []

        query = {}
        if user_id:
            query["_id"] = user_id
        if email:
            query["email"] = email
        if user_role:
            query["roles"] = user_role.value

        response = await Users.data_service.find_by_query(
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
        update_password_hash: Optional[str] = None,
        increment_failed_login_attempts: Optional[bool] = None,
    ):
        query = {}
        if query_user_id:
            query["_id"] = str(query_user_id)

        update_request = {"$set": {}}
        if update_last_login_time:
            update_request["$set"]["last_login_time"] = update_last_login_time
        if update_job_title:
            update_request["$set"]["job_title"] = update_job_title
        if update_avatar:
            update_request["$set"]["avatar"] = update_avatar
        if update_account_state:
            update_request["$set"]["state"] = update_account_state.value
        if update_failed_login_attempts:
            update_request["$set"]["failed_login_attempts"] = update_failed_login_attempts
        if increment_failed_login_attempts:
            update_request["$inc"] = {"failed_login_attempts": 1}
        if update_password_hash:
            update_request["$set"]["hashed_password"] = update_password_hash

        update_response = await Users.data_service.update_many(
            collection=Users.DB_COLLECTION_USERS,
            query=query,
            data=jsonable_encoder(update_request),
        )

        if update_response.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found or no changes to update",
            )
