from __future__ import annotations

from litestar import Litestar

from apps.storage_app.server.routers.download_router import router

# ------------------------------------------------------------
# Litestar アプリ本体
# ------------------------------------------------------------
app = Litestar(
    route_handlers=[
        router,
    ],
    debug=True
)
