import time
import requests
import warnings
from fixlib.logger import log
from fixlib.args import ArgumentParser
from urllib.parse import urlparse, ParseResult
from typing import Optional, Dict


class CLIEnvelope:
    """
    Envelope fields that are used by the CLI.
    Those fields are encoded as HTTP Headers into the HTTP response.
    """

    # Defines the action that should be performed.
    # Use cases:
    # - "edit": A file that is returned from the core should be opened in an editor.
    #           The result of the edit should be sent back to the core, identified by the "command" envelope field.
    action = "Fix-Shell-Action"
    # Defines the command that should be executed after the edit was performed.
    command = "Fix-Shell-Command"
    # Do not add this command to the shell history.
    no_history = "Fix-Shell-No-History"


def add_args(arg_parser: ArgumentParser) -> None:
    pass


def fixcore_is_up(fixcore_uri: str, timeout: int = 5, headers: Optional[Dict[str, str]] = None) -> bool:
    pass


def wait_for_fixcore(fixcore_uri: str, timeout: int = 300, headers: Optional[Dict[str, str]] = None) -> None:
    pass


class FixcoreURI:
    def __init__(self, fixcore_uri: Optional[str] = None) -> None:
        self.fixcore_uri = fixcore_uri

    @property
    def uri(self) -> ParseResult:
        pass

    @property
    def http_uri(self) -> str:
        pass

    @property
    def ws_uri(self) -> str:
        pass

    @property
    def is_secure(self) -> bool:
        pass


fixcore = FixcoreURI()
