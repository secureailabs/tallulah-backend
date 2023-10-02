# -------------------------------------------------------------------------------
# Engineering
# authentication.py
# -------------------------------------------------------------------------------
"""Tallulah authentication and authorization service"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from datetime import datetime
from time import time
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models.accounts import User_Db, UserAccountState, UserInfo_Out, UserRole, Users
from app.models.authentication import LoginSuccess_Out, RefreshToken_In, TokenData
from app.models.common import BasicObjectInfo, PyObjectId
from app.utils.secrets import get_secret

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

# Authentication settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_password_hash(salt, password):
    password_pepper = get_secret("password_pepper")
    return pwd_context.hash(f"{salt}{password}{password_pepper}")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_secret("jwt_secret"), algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        user_id = token_data.id
        if not user_id:
            raise credentials_exception
    except JWTError as exception:
        raise credentials_exception
    return token_data


class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: TokenData = Depends(get_current_user)):
        # allow SAIL_ADMIN to do anything
        if UserRole.SAIL_ADMIN in user.roles:
            return None

        if user.roles:
            for role in user.roles:
                if role in self.allowed_roles:
                    return None
            raise HTTPException(status_code=403, detail="Operation not permitted")


@router.post(
    path="/login",
    description="User login with email and password",
    response_model=LoginSuccess_Out,
    response_model_by_alias=False,
    operation_id="login",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> LoginSuccess_Out:
    """
    User login with email and password

    :param form_data: email and password of the user
    :type form_data: OAuth2PasswordRequestForm, optional
    :return: access token and refresh token
    :rtype: LoginSuccess_Out
    """

    exception_authentication_failed = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    found_user = await Users.read(email=form_data.username, throw_on_not_found=False)
    if not found_user:
        raise exception_authentication_failed
    found_user_db = found_user[0]

    if found_user_db.account_state is not UserAccountState.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"User account is {found_user_db.account_state.value}. Contact SAIL support.",
        )

    password_pepper = get_secret("password_pepper")
    if not pwd_context.verify(
        secret=f"{found_user_db.email}{form_data.password}{password_pepper}",
        hash=found_user_db.hashed_password,
    ):
        # If this is a 5th failed attempt, lock the account and increase the failed login attempts
        # Otherwise, just increase the failed login attempts
        if found_user_db.failed_login_attempts >= 4:
            await Users.update(
                query_user_id=found_user_db.id,
                update_account_state=UserAccountState.LOCKED,
                increment_failed_login_attempts=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password. Account locked."
            )
        else:
            await Users.update(query_user_id=found_user_db.id, increment_failed_login_attempts=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Incorrect username or password. {4 - found_user_db.failed_login_attempts} attempts left.",
            )
    else:
        # Reset the failed login attempts and update the last login time
        await Users.update(
            query_user_id=found_user_db.id, update_last_login_time=datetime.utcnow(), update_failed_login_attempts=0
        )

    # Create the access token and refresh token and return them
    token_data = TokenData(
        _id=found_user_db.id,
        roles=found_user_db.roles,
        exp=int((time() * 1000) + (ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000)),
    )
    access_token = jwt.encode(
        claims=jsonable_encoder(token_data),
        key=get_secret("jwt_secret"),
        algorithm=ALGORITHM,
    )
    refresh_token = jwt.encode(
        claims=jsonable_encoder(token_data),
        key=get_secret("refresh_secret"),
        algorithm=ALGORITHM,
    )

    return LoginSuccess_Out(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post(
    path="/refresh-token",
    description="Refresh the JWT token for the user",
    response_model=LoginSuccess_Out,
    operation_id="get_refresh_token",
)
async def refresh_for_access_token(
    refresh_token_request: RefreshToken_In = Body(description="Refresh token request"),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials."
    )
    try:
        # TODO: Prawal harden the security around the refresh token
        payload = jwt.decode(refresh_token_request.refresh_token, get_secret("refresh_secret"), algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        user_id = token_data.id
        if not user_id:
            raise credentials_exception

        found_user = await Users.read(user_id=user_id, throw_on_not_found=False)
        if not found_user:
            raise credentials_exception

        found_user_db = found_user[0]
        token_data = TokenData(
            **found_user_db.dict(), exp=int((time() * 1000) + (ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000))
        )

        access_token = jwt.encode(
            claims=jsonable_encoder(token_data),
            key=get_secret("jwt_secret"),
            algorithm=ALGORITHM,
        )

        refresh_token = jwt.encode(
            claims=jsonable_encoder(token_data),
            key=get_secret("refresh_secret"),
            algorithm=ALGORITHM,
        )

    except JWTError as exception:
        raise credentials_exception

    return LoginSuccess_Out(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.get(
    path="/me",
    description="Get the current user information",
    response_description="The current user information",
    response_model=UserInfo_Out,
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK,
    operation_id="get_current_user_info",
)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
) -> UserInfo_Out:
    found_user = await Users.read(user_id=current_user.id)

    return UserInfo_Out(**found_user[0].dict())


@router.put(
    path="/unlock-account/{user_id}",
    description="Unlock the user account",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RoleChecker(allowed_roles=[]))],
    operation_id="unlock_user_account",
)
async def unlock_user_account(
    user_id: PyObjectId = Path(description="The user id to unlock the account for"),
    _: User_Db = Depends(get_current_user),
):
    # Update the user account state and reset the failed login attempts to 0
    await Users.update(
        query_user_id=user_id, update_account_state=UserAccountState.ACTIVE, update_failed_login_attempts=0
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
