from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Dict, Any, List

from litestar import Router, get, post, Request
from litestar.exceptions import HTTPException

from litestar.response import Stream
cdc_connections: Dict[str, List[asyncio.Queue[str]]] = {}


@post("/relay")
async def cdc_relay(request: Request) -> Dict[str, str]:
    payload = await request.json()

    if not payload:
        raise HTTPException(status_code=400, detail="no payload")

    record_id = payload.get("id")
    if not record_id:
        raise HTTPException(status_code=400, detail="no id")

    queues = cdc_connections.setdefault(record_id, [])
    data = json.dumps(payload, ensure_ascii=False)

    for q in queues:
        await q.put(data)

    return {"status": "received"}


async def cdc_event_stream(record_id: str):
    queue: asyncio.Queue[str] = asyncio.Queue()
    cdc_connections.setdefault(record_id, []).append(queue)

    try:
        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=25)
                # JSON を SSE の data 行として送る
                yield f"data: {data}\n\n"
            except asyncio.TimeoutError:
                # heartbeat はコメント
                yield ": heartbeat\n\n"
    finally:
        cdc_connections[record_id].remove(queue)


from litestar.response import Stream

@get("/stream/{record_id:str}")
async def cdc_stream(record_id: str) -> Stream:
    return Stream(
        content=cdc_event_stream(record_id),
        media_type="text/event-stream",
    )

cdc_router = Router(
    path="/services/data/v60.0/cdc",
    route_handlers=[cdc_relay, cdc_stream],
)
