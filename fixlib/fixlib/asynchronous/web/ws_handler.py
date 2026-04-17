import asyncio
from asyncio import Queue, Future
from contextlib import suppress
from typing import (
    Callable,
    Awaitable,
    AsyncContextManager,
    Any,
    Optional,
    Sequence,
    Dict,
    Tuple,
    TypeVar,
)
from uuid import uuid1

import jsons
from aiohttp import WSMessage, WSMsgType
from aiohttp.web import Request, WebSocketResponse

from fixlib.logger import log

WSHandler = Dict[str, Tuple[Future[Any], WebSocketResponse]]
T = TypeVar("T")


async def clean_ws_handler(ws_id: str, websocket_handler: WSHandler) -> None:
    with suppress(Exception):
        handler = websocket_handler.get(ws_id)
        if handler:
            websocket_handler.pop(ws_id, None)
            future, ws = handler
            future.cancel()
            log.info(f"Cleanup ws handler: {ws_id} ({len(websocket_handler)} active)")
            if not ws.closed:
                await ws.close()


def js_str(a: Any) -> str:
    pass


async def accept_websocket(
    request: Request,
    *,
    handle_incoming: Callable[[str], Awaitable[None]],
    websocket_handler: WSHandler,
    outgoing_context: Optional[Callable[[], AsyncContextManager[Queue[T]]]] = None,
    initial_messages: Optional[Sequence[Any]] = None,
    outgoing_fn: Callable[[T], str] = js_str,
) -> WebSocketResponse:
    pass
