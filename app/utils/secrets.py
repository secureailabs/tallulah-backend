# -------------------------------------------------------------------------------
# Engineering
# secrets.py
# -------------------------------------------------------------------------------
"""Get secrets"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Array Insights, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Array Insights, Inc.
# -------------------------------------------------------------------------------

import os
from typing import Dict

initialization_vector: Dict[str, str] = {}


def get_secret(secret_name: str) -> str:
    global initialization_vector

    if secret_name not in initialization_vector:
        # read from environment variable
        if secret_name in os.environ:
            initialization_vector[secret_name] = os.environ[secret_name]
        else:
            raise Exception(f"Secret {secret_name} not found")

    return initialization_vector[secret_name]
