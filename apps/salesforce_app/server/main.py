from __future__ import annotations

from litestar import Litestar

from apps.salesforce_app.server.routers.apex_router import apex_router
from apps.salesforce_app.server.routers.auth_router import auth_router
from apps.salesforce_app.server.routers.lwc_router import lwc_router
from apps.salesforce_app.server.routers.cdc_router import cdc_router
from apps.salesforce_app.server.routers.restapi_router import restapi_router
from apps.salesforce_app.server.routers.composite_router import router as composite_router
# ------------------------------------------------------------
# Litestar アプリ本体
# ------------------------------------------------------------
app = Litestar(
    route_handlers=[
        lwc_router,          # LWC のダウンロード API
        auth_router,         # OAuth2 Mock
        apex_router,         # Apex API
        cdc_router,          # CDC SSE
        restapi_router,      # Salesforce REST API
        composite_router,
    ],
    debug=True
)
