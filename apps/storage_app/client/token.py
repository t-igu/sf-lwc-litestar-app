# storage_server/app/worker/token.py

from __future__ import annotations
import time
from pathlib import Path
import httpx
import jwt  # PyJWT

from apps.const import (
    SF_URL_TOKEN,
    SF_GRANT_TYPE_JWT,
    SF_CLIENT_ID,
    SF_USERNAME,
    SF_AUDIENCE,
    SF_PRIVATE_KEY_PATH,
)
from apps.storage_app.utils.logging_decorator import trace_action


TOKEN_CACHE: str | None = None
TOKEN_EXPIRES_AT: float | None = None


def clear_token_cache():
    global TOKEN_CACHE, TOKEN_EXPIRES_AT
    TOKEN_CACHE = None
    TOKEN_EXPIRES_AT = None


def _create_jwt_assertion() -> str:
    """
    Salesforce JWT Bearer Flow 用の assertion を生成する。
    """
    private_key = Path(SF_PRIVATE_KEY_PATH).read_text()

    now = int(time.time())
    payload = {
        "iss": SF_CLIENT_ID,   # Connected App の Consumer Key
        "sub": SF_USERNAME,    # Integration User
        "aud": SF_AUDIENCE,    # login.salesforce.com または test.salesforce.com
        "exp": now + 180,      # 3分以内
    }

    return jwt.encode(payload, private_key, algorithm="RS256")


@trace_action
async def get_salesforce_token() -> str|None:
    """
    Salesforce JWT Bearer Flow によるアクセストークン取得。
    キャッシュが有効なら再利用する。
    """
    global TOKEN_CACHE, TOKEN_EXPIRES_AT

    # キャッシュが有効なら再利用
    if TOKEN_CACHE and TOKEN_EXPIRES_AT and TOKEN_EXPIRES_AT > time.time():
        return TOKEN_CACHE

    assertion = _create_jwt_assertion()

    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            SF_URL_TOKEN,
            data={
                "grant_type": SF_GRANT_TYPE_JWT,
                "assertion": assertion,
            },
        )

    res.raise_for_status()
    data = res.json()

    # キャッシュ更新
    TOKEN_CACHE = data["access_token"]
    TOKEN_EXPIRES_AT = time.time() + data.get("expires_in", 3600) - 30

    return TOKEN_CACHE
