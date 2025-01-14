# -------------------------------------------------------------------------------
# Engineering
# accounts.py
# -------------------------------------------------------------------------------
""" APIs to manage user accounts and organizations """
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------


from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Response, status

from app.api.authentication import RoleChecker, create_firebase_user, get_current_user, get_password_hash
from app.models.accounts import (
    GetMultipleUsers_Out,
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
from app.models.common import PyObjectId
from app.models.organizations import GetMultipleOrganizations_Out, GetOrganizations_Out, Organization_Db, Organizations
from app.utils.secrets import secret_store

router = APIRouter(tags=["users"])


@router.post(
    path="/api/users",
    description="Register new user",
    response_model=RegisterUser_Out,
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker(allowed_roles=[]))],
    operation_id="register_user",
)
async def register_user(
    user: RegisterUser_In = Body(description="User details to register with the organization"),
    _: TokenData = Depends(get_current_user),
) -> RegisterUser_Out:
    # Make the user's email lowercase
    user.email = user.email.strip().lower()

    # Check if the organization exists
    if user.organization_id:
        organization = await Organizations.read(organization_id=user.organization_id, throw_on_not_found=True)
        organization = organization[0]
    elif user.organization_name:
        # organization with same same should not exist
        organizations = await Organizations.read(name=user.organization_name, throw_on_not_found=False)
        if organizations:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization already exists")

        organization = Organization_Db(
            name=user.organization_name,
            admin=user.email,
        )
        await Organizations.create(organization=organization)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not provided")

    # Check if the user already exists
    user_db = await Users.read(email=user.email, throw_on_not_found=False)
    if user_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    # Also, don't allow the user to have a TALLULAH_ADMIN role
    if UserRole.TALLULAH_ADMIN in user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    # Create the user and add it to the database
    user_db = User_Db(
        name=user.name,
        organization_id=organization.id,
        email=user.email,
        roles=user.roles,
        job_title=user.job_title,
        hashed_password=get_password_hash(user.email, user.password),
        state=UserAccountState.ACTIVE,
    )
    await Users.create(user=user_db)

    await create_firebase_user(user.email, user.password, user.name)

    return RegisterUser_Out(id=user_db.id)


@router.get(
    path="/api/users/{user_id}",
    description="Get information about a user",
    response_model=GetUsers_Out,
    response_model_by_alias=False,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    operation_id="get_user",
)
async def get_user(
    user_id: PyObjectId = Path(description="UUID of the user"),
    _: TokenData = Depends(get_current_user),
) -> GetUsers_Out:
    # Check if the user exists
    user_db = await Users.read(user_id=user_id)

    return GetUsers_Out(**user_db[0].dict())


@router.get(
    path="/api/users",
    description="Get all users",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(allowed_roles=[]))],
    operation_id="get_all_users",
)
async def get_all_users(
    _: TokenData = Depends(get_current_user),
    organization_id: Optional[PyObjectId] = Query(default=None, description="UUID of the organization"),
) -> GetMultipleUsers_Out:
    # Check if the organization exists
    if organization_id:
        await Organizations.read(organization_id=organization_id, throw_on_not_found=True)

    users = await Users.read(organization_id=organization_id)

    return GetMultipleUsers_Out(users=[GetUsers_Out(**user.dict()) for user in users])


@router.get(
    path="/api/organizations",
    description="Get all organizations",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(allowed_roles=[]))],
    operation_id="get_all_organizations",
)
async def get_all_organizations(
    _: TokenData = Depends(get_current_user),
) -> GetMultipleOrganizations_Out:
    organizations = await Organizations.read()

    return GetMultipleOrganizations_Out(organizations=[GetOrganizations_Out(**org.dict()) for org in organizations])


@router.patch(
    path="/api/users/{user_id}",
    description="Update user information.",
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
    elif UserRole.TALLULAH_ADMIN in current_user.roles:
        pass
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    # Other info can be updated by org admin, sail admin or the user itself
    await Users.update(
        query_user_id=user_id,
        update_job_title=update_user_info.job_title,
        update_roles=update_user_info.roles,
        update_avatar=update_user_info.avatar,
        update_account_state=update_user_info.account_state,
        update_phone=update_user_info.phone,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    path="/api/users/{user_id}",
    description="Soft Delete user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="soft_delete_user",
)
async def soft_delete_user(
    user_id: PyObjectId = Path(description="UUID of the user"),
    current_user: TokenData = Depends(get_current_user),
):
    # User must be admin of same organization or should be a SAIL Admin or same user
    if user_id == current_user.id or UserRole.TALLULAH_ADMIN in current_user.roles:
        pass
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    await Users.update(
        query_user_id=user_id,
        update_account_state=UserAccountState.INACTIVE,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Add the sail admin user at the time of deployment
# @router.on_event("startup")
async def add_tallulah_admin():
    # Check if the organization exists
    organizations = await Organizations.read(name="Array Insights", throw_on_not_found=False)
    if organizations:
        organization = organizations[0]
    else:
        organization = Organization_Db(
            name="Array Insights",
            admin="admin@tallulah.net",
        )
        await Organizations.create(organization=organization)

    # Check if the user already exists
    user_db = await Users.read(user_role=UserRole.TALLULAH_ADMIN, throw_on_not_found=False)
    if user_db:
        return

    admin_email = "admin@tallulah.net"
    admin_name = "Tallulah Admin"

    # Create the user and add it to the database
    user_db = User_Db(
        name=admin_name,
        organization_id=organization.id,
        email=admin_email,
        roles=[UserRole.TALLULAH_ADMIN],
        job_title="Array Insights Admin",
        hashed_password=get_password_hash("admin@tallulah.net", secret_store.TALLULAH_ADMIN_PASSWORD),
        state=UserAccountState.ACTIVE,
    )

    await Users.create(user=user_db)

    await create_firebase_user(admin_email, secret_store.TALLULAH_ADMIN_PASSWORD, admin_name)
