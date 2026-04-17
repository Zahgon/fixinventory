import asyncio
import logging
import sys
from ssl import SSLContext
from typing import Optional, Union, Awaitable, Callable, Type, List, cast

from aiohttp.abc import AbstractAccessLogger
from aiohttp.log import access_logger

# noinspection PyProtectedMember
from aiohttp.web import HostSequence, _cancel_tasks
from aiohttp.web_app import Application
from aiohttp.web_log import AccessLogger
from aiohttp.web_runner import GracefulExit, BaseSite, TCPSite, AppRunner


# This method is derived from aiohttp.web.run_app with additional steps:
# - it allows a callable that is executed on shutdown.
# - it does not swallow terminal exceptions
# - it exposes a http and https port
def run_app(
    app: Union[Application, Awaitable[Application]],
    on_shutdown: Callable[[], Awaitable[None]],
    host: Union[str, HostSequence],
    https_port: Optional[int],
    http_port: Optional[int],
    default_port: int,
    *,
    shutdown_timeout: float = 60.0,
    keepalive_timeout: float = 75.0,
    ssl_context: Optional[SSLContext] = None,
    print_cmd: Callable[..., None] = print,
    backlog: int = 128,
    access_log_class: Type[AbstractAccessLogger] = AccessLogger,
    access_log_format: str = AccessLogger.LOG_FORMAT,
    access_log: Optional[logging.Logger] = access_logger,
    handle_signals: bool = True,
    reuse_address: Optional[bool] = None,
    reuse_port: Optional[bool] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> None:
    """Run an app locally"""
    pass


async def _run_app(
    app: Union[Application, Awaitable[Application]],
    host: Union[str, HostSequence],
    https_port: Optional[int],
    http_port: Optional[int],
    default_port: int,
    *,
    shutdown_timeout: float = 60.0,
    keepalive_timeout: float = 75.0,
    ssl_context: Optional[SSLContext] = None,
    print: Optional[Callable[..., None]] = print,
    backlog: int = 128,
    access_log_class: Type[AbstractAccessLogger] = AccessLogger,
    access_log_format: str = AccessLogger.LOG_FORMAT,
    access_log: Optional[logging.Logger] = access_logger,
    handle_signals: bool = True,
    reuse_address: Optional[bool] = None,
    reuse_port: Optional[bool] = None,
) -> None:
    # An internal function to actually do all dirty job for application running
    pass
