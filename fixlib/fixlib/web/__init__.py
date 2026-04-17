import threading
import cherrypy
from fixlib.logger import log
from typing import Optional, Any


class WebServer(threading.Thread):
    def __init__(
        self,
        web_app: Any,
        web_host: str = "::",
        web_port: int = 9955,
        ssl_cert: Optional[str] = None,
        ssl_key: Optional[str] = None,
        extra_config: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self.name = "webserver"
        self.web_app = web_app
        self.web_host = web_host
        self.web_port = web_port
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.extra_config = extra_config or {}

    @property
    def serving(self) -> bool:
        pass

    def run(self) -> None:
        # CherryPy always prefixes its log messages with a timestamp.
        # The next line monkey patches that time method to return a
        # fixed string. So instead of having duplicate timestamps in
        # each web server related log message they are now prefixed
        # with the string 'CherryPy'.
        pass

    def shutdown(self) -> None:
        pass

    def mount(self, mountpoint: str, app: Any) -> None:
        pass
