# -------------------------------------------------------------------------------
# Engineering
# authentication.py
# -------------------------------------------------------------------------------
"""Models used by authentication services"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

from typing import List

from pydantic import Field, StrictStr

from app.models.accounts import UserRole
from app.models.common import PyObjectId, SailBaseModel


class LoginSuccess_Out(SailBaseModel):
    access_token: StrictStr
    refresh_token: StrictStr
    token_type: StrictStr


class ChartToken_Out(SailBaseModel):
    chart_token: StrictStr


class TokenData(SailBaseModel):
    id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    roles: List[UserRole] = Field()
    exp: int = Field()


class FirebaseTokenData(SailBaseModel):
    user_id: StrictStr = Field()
    email: StrictStr = Field()


class RefreshTokenData(SailBaseModel):
    id: PyObjectId = Field()
    organization_id: PyObjectId = Field()
    roles: List[UserRole] = Field()
    exp: int = Field()


class ResetPassword_In(SailBaseModel):
    current_password: StrictStr = Field()
    new_password: StrictStr = Field()


class RefreshToken_In(SailBaseModel):
    refresh_token: StrictStr = Field()
