from __future__ import annotations

import json
import queue
import threading
import time
from typing import Callable, Dict, Optional, List, Any
from urllib.parse import urlunsplit, urlsplit

from attrs import define, field
from websocket import WebSocketApp, WebSocket

from fixlib.args import ArgumentParser
from fixlib.baseresources import BaseResource
from fixlib.config import current_config
from fixlib.core.ca import TLSData
from fixlib.core.custom_command import CommandDefinition
from fixlib.core.model_export import node_to_dict, node_from_dict
from fixlib.event import EventType, remove_event_listener, add_event_listener, Event
from fixlib.json import to_json_str
from fixlib.jwt import encode_jwt_to_headers
from fixlib.logger import log
from fixlib.types import Json, JsonElement


@define
class CoreTaskResult:
    task_id: str
    data: JsonElement = None
    error: Optional[str] = None

    def to_json(self) -> Json:
        if self.error:
            return {"task_id": self.task_id, "result": "error", "error": self.error}
        else:
            return {"task_id": self.task_id, "result": "done", "data": self.data}


@define
class CoreTaskHandler:
    name: str
    info: str
    description: str
    handler: Callable[[Json], JsonElement]
    expect_node_result: bool = False
    filter: Dict[str, List[str]] = field(factory=dict)
    allowed_on_kind: Optional[str] = None
    args_description: Dict[str, str] = field(factory=dict)

    def execute(self, message: Json) -> CoreTaskResult:
        task_id = message["task_id"]  # fail if there is no task_id
        try:
            task_data: Json = message.get("data", {})
            result = self.handler(task_data)
            return CoreTaskResult(task_id=task_id, data=result)
        except Exception as e:
            log.debug(f"Error while executing task {self.name}: {e}", exc_info=True)
            return CoreTaskResult(task_id=task_id, error=str(e))

    def matches(self, js: Json) -> bool:
        attrs: Json = js.get("attrs", {})
        if js.get("task_name") != self.name or not isinstance(attrs, dict):
            return False
        return all((attrs.get(n) in f) for n, f in self.filter.items())

    def core_json(self) -> Json:
        pass

    @staticmethod
    def from_definition(target: Any, wtd: CommandDefinition) -> CoreTaskHandler:
        pass


class CoreTasks(threading.Thread):
    def __init__(
        self,
        identifier: str,
        fixcore_ws_uri: str,
        task_handler: List[CoreTaskHandler],
        max_workers: int = 20,
        tls_data: Optional[TLSData] = None,
    ) -> None:
        super().__init__()
        self.identifier = identifier
        self.fixcore_ws_uri = fixcore_ws_uri
        self.task_handler = task_handler
        self.max_workers = max_workers
        self.tls_data = tls_data
        self.ws: Optional[WebSocketApp] = None
        self.shutdown_event = threading.Event()
        self.queue: queue.Queue[Json] = queue.Queue()
        self.__connected = False

    def connected(self) -> bool:
        pass

    def __del__(self) -> None:
        remove_event_listener(EventType.SHUTDOWN, self.shutdown)

    def run(self) -> None:
        pass

    def worker(self) -> None:
        while not self.shutdown_event.is_set():
            message = self.queue.get()
            log.debug(f"{self.identifier} received: {message}")
            for handler in self.task_handler:
                if handler.matches(message):
                    try:
                        result = handler.execute(message)
                        if self.ws:
                            log.debug(f"Sending reply {result.to_json()}")
                            self.ws.send(json.dumps(result.to_json()))
                    except Exception as ex:
                        log.exception(f"Something went wrong while processing {message}")
                        if (task_id := message.get("task_id")) and self.ws is not None:
                            self.ws.send(to_json_str(CoreTaskResult(task_id, error=str(ex)).to_json()))
                    break
            self.queue.task_done()

    def connect(self) -> None:
        fixcore_ws_uri_split = urlsplit(self.fixcore_ws_uri)
        scheme = fixcore_ws_uri_split.scheme
        netloc = fixcore_ws_uri_split.netloc
        path = fixcore_ws_uri_split.path + "/work/queue"
        ws_uri = urlunsplit((scheme, netloc, path, "", ""))

        log.debug(f"{self.identifier} connecting to {ws_uri}")
        headers: Dict[str, str] = {}
        if getattr(ArgumentParser.args, "psk", None):
            encode_jwt_to_headers(headers, {}, ArgumentParser.args.psk)
        self.ws = WebSocketApp(
            ws_uri,
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_ping=self.on_ping,
            on_pong=self.on_pong,
        )
        sslopt: Dict[Any, Any] = {}
        if self.tls_data:
            sslopt = {"ca_certs": self.tls_data.ca_cert_path}
        self.ws.run_forever(sslopt=sslopt, ping_interval=20, ping_timeout=10, ping_payload="ping")

    def shutdown(self, _: Optional[Event] = None) -> None:
        pass

    def on_message(self, _: WebSocket, message: str) -> None:
        pass

    def on_error(self, _: WebSocket, e: Exception) -> None:
        pass

    def on_close(self, _: WebSocket, close_status_code: int, close_msg: str) -> None:
        pass

    def on_open(self, ws: WebSocket) -> None:
        pass

    def on_ping(self, _: WebSocket, message: str) -> None:
        pass

    def on_pong(self, _: WebSocket, message: str) -> None:
        pass
