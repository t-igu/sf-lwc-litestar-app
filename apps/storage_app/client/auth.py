# storage_server/app/worker/auth.py

from __future__ import annotations
import datetime
import jwt

from apps.const import (
    SF_CLIENT_ID,
    SF_USERNAME,
    SF_AUDIENCE,
    SF_PRIVATE_KEY,
)

# ------------------------------------------------------------
# JWT Assertion 作成（Worker → Salesforce Token Endpoint）
# ------------------------------------------------------------
def create_jwt_assertion() -> str:
    """
    Salesforce JWT Bearer Flow 用の JWT assertion を生成する。
    """
    now = datetime.datetime.now(datetime.timezone.utc)

    payload = {
        "iss": SF_CLIENT_ID,
        "sub": SF_USERNAME,
        "aud": SF_AUDIENCE,
        "exp": now + datetime.timedelta(minutes=3),
    }

    token = jwt.encode(
        payload,
        SF_PRIVATE_KEY,
        algorithm="RS256",
    )

    return token
