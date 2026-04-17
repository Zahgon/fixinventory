import threading
import time
from contextlib import suppress, AbstractContextManager
from itertools import islice
from logging import Logger
from queue import Queue

from websocket import WebSocketApp, WebSocket
import requests
import json
from concurrent.futures import ThreadPoolExecutor

from attr import define, evolve, field
from requests import Response

from fixlib.core.progress import Progress, ProgressDone
from fixlib.logger import log
from fixlib.event import EventType, remove_event_listener, add_event_listener, Event
from fixlib.args import ArgumentParser
from fixlib.jwt import encode_jwt_to_headers
from fixlib.core.ca import TLSData
from typing import Callable, Dict, Optional, List, Any, Set

from fixlib.types import Json
from fixlib.utils import utc_str


@define(frozen=True)
class CoreFeedback:
    task_id: str
    step_name: str
    message_type: str
    core_messages: Queue[Json]
    context: List[str] = field(factory=list)

    def progress_done(self, name: str, current: int, total: int, context: Optional[List[str]] = None) -> None:
        pass

    def progress(self, progress: Progress) -> None:
        pass

    def info(self, message: str, logger: Optional[Logger] = None) -> None:
        if logger:
            logger.warning(self.context_str + message)
        self._info_message("info", message)

    def error(self, message: str, logger: Optional[Logger] = None) -> None:
        if logger:
            logger.warning(self.context_str + message, exc_info=True)
        self._info_message("error", message)

    @property
    def context_str(self) -> str:
        pass

    def _info_message(self, level: str, message: str) -> None:
        self.core_messages.put(
            {
                "kind": "action_info",
                "message_type": self.message_type,
                "data": {
                    "task": self.task_id,
                    "step": self.step_name,
                    "level": level,
                    "message": self.context_str + message[0:500],  # truncate message to 500 characters
                },
            }
        )

    def with_context(self, *context: str) -> "CoreFeedback":
        pass

    def child_context(self, *context: str) -> "CoreFeedback":
        pass


@define
class ErrorSummary:
    error: str
    message: str
    info: bool
    region: Optional[str] = None
    service_actions: Dict[str, Set[str]] = field(factory=dict)


class ErrorAccumulator:
    def __init__(self) -> None:
        self.regional_errors: Dict[Optional[str], Dict[str, ErrorSummary]] = {}

    def add_error(
        self, as_info: bool, error_kind: str, service: str, action: str, message: str, region: Optional[str] = None
    ) -> None:
        pass

    def report_region(self, core_feedback: CoreFeedback, region: Optional[str]) -> None:
        pass

    def report_all(self, core_feedback: CoreFeedback) -> None:
        pass


class SuppressWithFeedback(AbstractContextManager[None]):
    def __init__(self, message: str, feedback: CoreFeedback, logger: Optional[Logger] = None) -> None:
        self.message = message
        self.feedback = feedback
        self.logger = logger

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Optional[bool]:
        if exc_type is not None:
            self.feedback.error(f"{self.message}: {exc_val}", self.logger)
            return True  # suppress exception
        return None


class CoreActions(threading.Thread):
    def __init__(
        self,
        identifier: str,
        fixcore_uri: str,
        fixcore_ws_uri: str,
        actions: Dict[str, Json],
        incoming_messages: Optional[Queue[Json]] = None,
        message_processor: Optional[Callable[[Json], Any]] = None,
        tls_data: Optional[TLSData] = None,
        max_concurrent_actions: int = 5,
    ) -> None:
        super().__init__()
        self.identifier = identifier
        self.fixcore_uri = fixcore_uri
        self.fixcore_ws_uri = fixcore_ws_uri
        self.actions = actions
        self.message_processor = message_processor
        self.ws: Optional[WebSocketApp] = None
        self.incoming_messages = incoming_messages
        self.tls_data = tls_data
        self.shutdown_event = threading.Event()
        # one thread is taken by the queue listener
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_actions + 1, thread_name_prefix=self.identifier)
        self.__connected = False

    def connected(self) -> bool:
        pass

    def run(self) -> None:
        pass

    def wait_for_ws(self, timeout: int = 10) -> bool:
        pass

    def connect(self) -> None:
        for event, data in self.actions.items():
            if not isinstance(data, dict):
                data = None
            self.register(event, data)

        ws_uri = f"{self.fixcore_ws_uri}/subscriber/{self.identifier}/handle"
        log.debug(f"{self.identifier} connecting to {ws_uri}")
        headers: Dict[str, str] = {}
        if getattr(ArgumentParser.args, "psk", None):
            encode_jwt_to_headers(headers, {}, ArgumentParser.args.psk)
        try:
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
        finally:
            self.ws = None

    def shutdown(self, _: Optional[Event] = None) -> None:
        pass

    def register(self, action: str, data: Optional[Dict[str, str]] = None) -> bool:
        log.debug(f"{self.identifier} registering for {action} actions ({data})")
        return self.registration(action, requests.post, data)

    def unregister(self, action: str, data: Optional[Dict[str, str]] = None) -> bool:
        pass

    def registration(
        self,
        action: str,
        client: Callable[..., Response],
        data: Optional[Dict[str, str]] = None,
    ) -> bool:
        url = f"{self.fixcore_uri}/subscriber/{self.identifier}/{action}"
        headers = {"accept": "application/json"}

        if getattr(ArgumentParser.args, "psk", None):
            encode_jwt_to_headers(headers, {}, ArgumentParser.args.psk)

        verify = None
        if self.tls_data:
            verify = self.tls_data.ca_cert_path

        r = client(url, headers=headers, params=data, verify=verify)
        if r.status_code != 200:
            raise RuntimeError(f'Error during (un)registration for "{action}"' f" actions: {r.content.decode('utf-8')}")
        return True

    def on_message(self, _: WebSocket, message: str) -> None:
        pass

    def process_message(self, message: str) -> None:
        pass

    def on_error(self, _: WebSocket, e: Exception) -> None:
        pass

    def on_close(self, _: WebSocket, close_status_code: int, close_msg: str) -> None:
        pass

    def on_open(self, _: WebSocket) -> None:
        pass

    def on_ping(self, _: WebSocket, message: str) -> None:
        pass

    def on_pong(self, _: WebSocket, message: str) -> None:
        pass

    @staticmethod
    def add_args(arg_parser: ArgumentParser) -> None:
        pass
