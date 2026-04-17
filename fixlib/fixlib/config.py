import threading
import os

from fixlib.json import from_json, to_json
from fixlib.logger import log
from fixlib.args import ArgumentParser, convert
from fixlib.core.ca import TLSData
from fixlib.proc import restart
from fixlib.core.model_export import dataclasses_to_fixcore_model, optional_origin
from fixlib.core import FixcoreURI
from fixlib.core.config import (
    get_config,
    set_config,
    ConfigNotFoundError,
    update_config_model,
)
from fixlib.core.events import CoreEvents
from fixlib.utils import replace_env_vars, merge_json_elements, drop_deleted_attributes
from fixlib.types import Json
from typing import Dict, Any, List, Optional, Type, cast
from attrs import fields


class RunningConfig:
    def __init__(self) -> None:
        """Initialize the global config."""
        self.data: Dict[str, Any] = {}
        self.revision: str = ""
        self.classes: Dict[str, type] = {}
        self.types: Dict[str, Dict[str, type]] = {}

    def apply(self, other: "RunningConfig") -> None:
        """Apply another config to this one.

        Only updates references, does not create a copy of the data.
        """
        pass


_config = RunningConfig()


class MetaConfig(type):
    def __getattr__(cls, name: str) -> Any:
        if name in _config.data:
            return _config.data[name]
        else:
            raise ConfigNotFoundError(f"No such config {name}")


class Config(metaclass=MetaConfig):
    running_config: RunningConfig = _config

    def __init__(
        self,
        config_name: str,
        fixcore_uri: Optional[str] = None,
        tls_data: Optional[TLSData] = None,
    ) -> None:
        self._config_lock = threading.Lock()
        self.config_name = config_name
        self._initial_load = True
        fixcore = FixcoreURI(fixcore_uri)
        self.fixcore_uri = fixcore.http_uri
        self.verify = None
        if tls_data:
            self.verify = tls_data.verify
        self._ce = CoreEvents(
            fixcore.ws_uri,
            events={"config-updated"},
            message_processor=self.on_config_event,
            tls_data=tls_data,
        )

    def __getattr__(self, name: str) -> Any:
        if name in self.running_config.data:
            return self.running_config.data[name]
        else:
            raise ConfigNotFoundError(f"No such config {name}")

    def connected(self) -> bool:
        pass

    def shutdown(self) -> None:
        pass

    @staticmethod
    def init_default_config() -> None:
        pass

    @staticmethod
    def add_config(config: object) -> None:
        """Add a config to the config manager.

        Takes a dataclass as input and adds its fields to the config store.
        Dataclass must have a kind ClassVar which specifies the top level config name.
        """
        pass

    def load_config(self, reload: bool = False) -> None:
        pass

    def with_default_config(self, raw_config_json: Json) -> Json:
        """
        Merges the raw config from the core with the default config and clean up deleted entries.
        """
        pass

    @staticmethod
    def read_config(config: Json, read_as_json: bool = False, reason: Optional[str] = None) -> Dict[str, Any]:
        pass

    @staticmethod
    def restart_required(new_config: Json) -> bool:
        pass

    @staticmethod
    def apply_path_overrides_resolve_env_vars(running_config: RunningConfig, config: Json) -> bool:
        # there was no config received from fixcore, keep defaults
        pass

    @staticmethod
    def override_config(running_config: RunningConfig) -> None:
        pass

    @staticmethod
    def cast_target_type(config_value: Any, current_value: Any, fallback_target_type: Optional[type]) -> object:
        pass

    @staticmethod
    def dict() -> Json:
        pass

    def save_config(self) -> None:
        pass

    def on_config_event(self, message: Dict[str, Any]) -> None:
        pass

    # the __hash__ and the __eq__ below is a workaround to make sure the outdated config is not cached by
    # a lru_cache decoartor after the config performed a self-update. It serves no other purpose.
    def __hash__(self) -> int:
        return hash(self.running_config.revision)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Config):
            return self.running_config.__dict__ == other.running_config.__dict__
        return False

    @property
    def model(self) -> List[Json]:
        """Return the config dataclass model in fixcore format"""
        pass

    @staticmethod
    def add_args(arg_parser: ArgumentParser) -> None:
        pass


# Note: the config is mutable.
def current_config() -> Config:
    # metaclass makes it possible to use the class as instance.
    # use this accessor here to get a typed instance of the config
    return Config  # type: ignore
