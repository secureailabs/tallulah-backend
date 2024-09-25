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

import json
from datetime import datetime
from time import time
from typing import List

import firebase_admin
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from firebase_admin.auth import verify_id_token
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.models.accounts import UpdateUser_In, User_Db, UserAccountState, UserInfo_Out, UserRole, Users
from app.models.authentication import FirebaseTokenData, LoginSuccess_Out, RefreshToken_In, ResetPassword_In, TokenData
from app.models.common import PyObjectId
from app.models.organizations import Organizations
from app.utils.emails import EmailAddress, EmailBody, Message, MessageResponse, OutlookClient, ToRecipient
from app.utils.secrets import secret_store

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(tags=["authentication"])

# Authentication settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Firebase
cred = ""
if secret_store.FIREBASE_CREDENTIALS_FILE:
    cred = secret_store.FIREBASE_CREDENTIALS_FILE
else:
    cred = json.loads(bytes.fromhex(secret_store.FIREBASE_CREDENTIALS).decode("utf-8"))
cred = firebase_admin.credentials.Certificate(cred)
firebase_admin.initialize_app(cred)


def get_password_hash(salt, password):
    PASSWORD_PEPPER = secret_store.PASSWORD_PEPPER
    return pwd_context.hash(f"{salt}{password}{PASSWORD_PEPPER}")


async def firebase_get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = verify_id_token(token)
        return FirebaseTokenData(**decoded_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def create_firebase_user(email: str, password: str, name: str):
    return await run_in_threadpool(
        lambda: firebase_admin.auth.create_user(
            email=email,
            password=password,
            display_name=name,
            email_verified=True,
            disabled=False,
        )
    )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, secret_store.JWT_SECRET, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        user_id = token_data.id
        if not user_id:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as exception:
        raise credentials_exception

    return token_data


class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: TokenData = Depends(get_current_user)):
        # allow TALLULAH_ADMIN to do anything
        if UserRole.TALLULAH_ADMIN in user.roles:
            return None

        if user.roles:
            for role in user.roles:
                if role in self.allowed_roles:
                    return None
            raise HTTPException(status_code=403, detail="Operation not permitted")


@router.get(
    path="/api/ssologin",
    description="User login with firebase token",
    response_model=LoginSuccess_Out,
    response_model_by_alias=False,
    operation_id="ssologin",
)
async def ssologin(
    current_user: FirebaseTokenData = Depends(firebase_get_current_user),
) -> LoginSuccess_Out:
    exception_authentication_failed = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Two alternatives:
    # 1. We can either create custom firebase token and send it to client
    # 2. We can generate our own token -> Using this for now

    found_user = await Users.read(email=current_user.email, throw_on_not_found=False)
    if not found_user:
        raise exception_authentication_failed
    found_user_db = found_user[0]

    if found_user_db.state is not UserAccountState.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"User account is {found_user_db.state.value}. Contact Array Insights support.",
        )

    token_data = TokenData(
        id=found_user_db.id,
        roles=found_user_db.roles,
        organization_id=found_user_db.organization_id,
        exp=int(time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    access_token = jwt.encode(
        claims=jsonable_encoder(token_data),
        key=secret_store.JWT_SECRET,
        algorithm=ALGORITHM,
    )

    token_data.exp = int(time() + REFRESH_TOKEN_EXPIRE_MINUTES * 60)
    refresh_token = jwt.encode(
        claims=jsonable_encoder(token_data),
        key=secret_store.REFRESH_SECRET,
        algorithm=ALGORITHM,
    )

    return LoginSuccess_Out(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post(
    path="/api/login",
    description="User login with email and password",
    response_model=LoginSuccess_Out,
    response_model_by_alias=False,
    operation_id="login",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> LoginSuccess_Out:

    exception_authentication_failed = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    found_user = await Users.read(email=form_data.username.strip().lower(), throw_on_not_found=False)
    if not found_user:
        raise exception_authentication_failed
    found_user_db = found_user[0]

    if found_user_db.state is not UserAccountState.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"User account is {found_user_db.state.value}. Contact Array Insights support.",
        )

    if not pwd_context.verify(
        secret=f"{found_user_db.email.strip().lower()}{form_data.password}{secret_store.PASSWORD_PEPPER}",
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
        id=found_user_db.id,
        roles=found_user_db.roles,
        organization_id=found_user_db.organization_id,
        exp=int(time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    access_token = jwt.encode(
        claims=jsonable_encoder(token_data),
        key=secret_store.JWT_SECRET,
        algorithm=ALGORITHM,
    )
    token_data.exp = int(time() + REFRESH_TOKEN_EXPIRE_MINUTES * 60)
    refresh_token = jwt.encode(
        claims=jsonable_encoder(token_data),
        key=secret_store.REFRESH_SECRET,
        algorithm=ALGORITHM,
    )

    return LoginSuccess_Out(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post(
    path="/api/refresh-token",
    description="Refresh the JWT token for the user",
    response_model=LoginSuccess_Out,
    response_model_by_alias=False,
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
        payload = jwt.decode(refresh_token_request.refresh_token, secret_store.REFRESH_SECRET, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        user_id = token_data.id
        if not user_id:
            raise credentials_exception

        found_user = await Users.read(user_id=user_id, throw_on_not_found=False)
        if not found_user:
            raise credentials_exception

        found_user_db = found_user[0]
        token_data = TokenData(**found_user_db.dict(), exp=int(time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60))

        access_token = jwt.encode(
            claims=jsonable_encoder(token_data),
            key=secret_store.JWT_SECRET,
            algorithm=ALGORITHM,
        )

        token_data.exp = int(time() + REFRESH_TOKEN_EXPIRE_MINUTES * 60)
        refresh_token = jwt.encode(
            claims=jsonable_encoder(token_data),
            key=secret_store.REFRESH_SECRET,
            algorithm=ALGORITHM,
        )

    except JWTError as exception:
        raise credentials_exception

    return LoginSuccess_Out(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.get(
    path="/api/me",
    description="Get the current user information",
    response_description="The current user information",
    response_model=UserInfo_Out,
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK,
    operation_id="get_current_user_info",
)
async def get_current_user_info(
    current_user: UserInfo_Out = Depends(get_current_user),
) -> UserInfo_Out:
    found_user = await Users.read(user_id=current_user.id)

    # Get the user organization name
    organization = await Organizations.read(organization_id=found_user[0].organization_id)

    return UserInfo_Out(**found_user[0].dict(), organization_name=organization[0].name)


@router.post(
    path="/api/password-reset",
    description="Reset the user password",
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK,
    operation_id="reset_user_password",
)
async def reset_user_password(
    password_reset_req: ResetPassword_In = Body(description="Password reset request"),
    current_user: TokenData = Depends(get_current_user),
) -> Response:

    found_user = await Users.read(user_id=current_user.id)
    found_user = found_user[0]

    if not pwd_context.verify(
        secret=f"{found_user.email.lower()}{password_reset_req.current_password}{secret_store.PASSWORD_PEPPER}",
        hash=found_user.hashed_password,
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect current password")

    # Update the user password
    new_password_hash = get_password_hash(found_user.email.lower(), password_reset_req.new_password)
    await Users.update(query_user_id=found_user.id, update_password_hash=new_password_hash)

    return Response(status_code=status.HTTP_200_OK)


@router.put(
    path="/api/unlock-account/{user_id}",
    description="Unlock the user account",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RoleChecker(allowed_roles=[]))],
    operation_id="unlock_user_account",
)
async def unlock_user_account(
    user_id: PyObjectId = Path(description="The user id to unlock the account for"),
    _: TokenData = Depends(get_current_user),
):
    # Update the user account state and reset the failed login attempts to 0
    await Users.update(
        query_user_id=user_id, update_account_state=UserAccountState.ACTIVE, update_failed_login_attempts=0
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/api/auth/enable-2fa",
    description="Enable 2FA for the user",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="enable_2fa",
)
async def enable_2fa(
    current_user: FirebaseTokenData = Depends(firebase_get_current_user),
    update_user_info: UpdateUser_In = Body(description="User Object - only phone is considered"),
):
    found_user = await Users.read(email=current_user.email)
    found_user = found_user[0]
    if not update_user_info.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required")

    # Update phone
    firebase_admin.auth.update_user(current_user.user_id, email_verified=True, phone_number=update_user_info.phone)
    # Firebase Python sdk missing enrollment of 2fa, so this is done via web

    await Users.update(query_user_id=found_user.id, update_phone=update_user_info.phone, ignore_no_update=True)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/api/auth/migrate-users",
    description="Migrate users to firebase",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RoleChecker(allowed_roles=[]))],
    operation_id="migrate_users",
)
async def migrate_users(
    _: TokenData = Depends(get_current_user),
):
    users = await Users.read()
    for user in users:
        # find if user exists in firebase
        try:
            await run_in_threadpool(lambda: firebase_admin.auth.get_user_by_email(user.email))
            continue  # user already exists
        except firebase_admin.auth.UserNotFoundError:
            print(f"Processing user: {user.email}")
            pass
        # Create user in firebase
        await create_firebase_user(user.email, "arrayinsights", user.name)

        # Send password reset email
        reset_link = await run_in_threadpool(lambda: firebase_admin.auth.generate_password_reset_link(user.email))

        # Send email
        try:
            client = OutlookClient(
                client_id=secret_store.OUTLOOK_CLIENT_ID,
                client_secret=secret_store.OUTLOOK_CLIENT_SECRET,
                redirect_uri=secret_store.OUTLOOK_REDIRECT_URI,
            )
            await client.connect_with_refresh_token(secret_store.EMAIL_NO_REPLY_REFRESH_TOKEN)

            # Send email notifications to the subscribed users
            email_message = MessageResponse(
                message=Message(
                    subject="Tallulah just upgraded the authentication system!",
                    body=EmailBody(
                        contentType="html",
                        content=f'<html>We just upgraded our authentication system to a better one! <br> You can reset the password <a href="{reset_link}">here.</a></html>',
                    ),
                    toRecipients=[ToRecipient(emailAddress=EmailAddress(address=user.email, name=user.name))],
                )
            )
            await client.send_email(email_message)
        except:
            pass

    return Response(status_code=status.HTTP_204_NO_CONTENT)
