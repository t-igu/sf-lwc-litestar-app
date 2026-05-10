from __future__ import annotations

from datetime import datetime
import secrets
from typing import Dict, Any

from litestar import Router, post, Request
from litestar.exceptions import HTTPException

from apps.const import SF_AUDIENCE

# ------------------------------------------------------------
# Salesforce OAuth2 Token Endpoint (Mock)
# ------------------------------------------------------------
@post("/token")
async def issue_token(request: Request) -> Dict[str, Any]:
    """
    Salesforce OAuth2 Token Endpoint (Mock)
    Supports JWT Bearer Flow only
    """

    # FastAPI と同じ：multipart/form-data を form() で取得
    form = await request.form()

    grant_type = form.get("grant_type")
    if grant_type != "urn:ietf:params:oauth:grant-type:jwt-bearer":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    # assertion = form.get("assertion")
    # 本番では JWT decode & verify
    # Mock なので省略

    return {
        "access_token": "mock_access_token",
        "instance_url": SF_AUDIENCE,
        "token_type": "Bearer",
        "issued_at": str(int(datetime.utcnow().timestamp() * 1000)),
        "signature": secrets.token_hex(16),
    }


auth_router = Router(
    path="/services/oauth2",
    route_handlers=[issue_token],
)
