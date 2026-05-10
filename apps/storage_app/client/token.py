# storage_server/app/worker/token.py

from __future__ import annotations
import httpx

from apps.const import SF_URL_TOKEN, SF_GRANT_TYPE_JWT
from apps.storage_app.utils.logging_decorator import trace_action

TOKEN_CACHE = None

def clear_token_cache():
    global TOKEN_CACHE
    TOKEN_CACHE = None

@trace_action
async def get_salesforce_token():
    global TOKEN_CACHE

    if TOKEN_CACHE:
        return TOKEN_CACHE

    async with httpx.AsyncClient() as client:
        res = await client.post(
            SF_URL_TOKEN,
            data={"grant_type": SF_GRANT_TYPE_JWT},
        )

    res.raise_for_status()

    data = res.json()
    TOKEN_CACHE = data["access_token"]
    return TOKEN_CACHE
