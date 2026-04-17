import time
from abc import ABC, abstractmethod
from enum import Enum, auto
from queue import Queue
from threading import Thread, current_thread
from typing import Dict, Optional, Any

from prometheus_client import Counter

import fixlib.config
import fixlib.proc
from fixlib.args import ArgumentParser
from fixlib.baseresources import BaseResource, Cloud
from fixlib.config import Config
from fixlib.core import fixcore
from fixlib.core.actions import CoreActions
from fixlib.core.ca import TLSData
from fixlib.graph import Graph, GraphMergeKind, MaxNodesExceeded
from fixlib.logger import log
from fixlib.types import Json

metrics_unhandled_plugin_exceptions = Counter(
    "fix_unhandled_plugin_exceptions_total",
    "Unhandled plugin exceptions",
    ["plugin"],
)


class PluginType(Enum):
    """Defines Plugin Type

    COLLECTOR is a cloud resource collector plugin that gets instantiated
    on each collect() run
    PERSISTENT is a persistent plugin that gets instantiated once upon startup
    """

    COLLECTOR = auto()
    ACTION = auto()
    PERSISTENT = auto()
    CLI = auto()


class BasePlugin(ABC, Thread):
    """A fix Plugin is a thread that does some work.

    If the plugin_type is PluginType.COLLECTOR the Plugin gets instantiated each
    collect run.
    If the plugin_type is PluginType.PERSISTENT the Plugin gets instantiated upon
    startup and is expected to run forever. It may register to any events it's
    interested in and act upon them.

    Upon start the go() method is called. For COLLECTOR Plugins collect() is called.
    """

    plugin_type = PluginType.PERSISTENT

    def __init__(self) -> None:
        super().__init__()
        self.name = self.__class__.__name__
        self.finished = False

    def run(self) -> None:
        pass

    @abstractmethod
    def go(self) -> None:
        """Do the Plugin work"""
        pass

    @staticmethod
    def add_args(arg_parser: ArgumentParser) -> None:
        """Adds Plugin specific arguments to the global arg parser"""
        pass

    @staticmethod
    def add_config(config: Config) -> None:
        """Adds Plugin specific config options"""
        pass


class BaseActionPlugin(ABC, Thread):
    plugin_type = PluginType.ACTION
    action: str = NotImplemented  # Name of the action this plugin implements

    def __init__(self, tls_data: Optional[TLSData] = None) -> None:
        super().__init__()
        self._args = ArgumentParser.args
        self._config = fixlib.config._config
        self.name = self.__class__.__name__
        self.finished = False
        self.timeout = Config.fixworker.timeout
        self.wait_for_completion = True
        self.tls_data = tls_data

    @abstractmethod
    def do_action(self, data: Dict[str, Any]) -> None:
        """Perform an action"""
        pass

    def action_processor(self, message: Json) -> Optional[Json]:
        """Process incoming action messages"""
        pass

    def run(self) -> None:
        pass

    @abstractmethod
    def bootstrap(self) -> bool:
        """Bootstrap the plugin.

        If bootstrapping is successful the plugin is ready to run.
        """
        pass

    def go(self) -> None:
        pass

    @staticmethod
    def add_args(arg_parser: ArgumentParser) -> None:
        """Adds Plugin specific arguments to the global arg parser"""
        pass

    @staticmethod
    def add_config(config: Config) -> None:
        """Adds Plugin specific config options"""
        pass


class BaseCollectorPlugin(BasePlugin):
    """A fix Collector plugin is a thread that collects cloud resources.

    Whenever the thread is started the collect() method is run. The collect() method
    is expected to add cloud resources to self.graph. Cloud resources must inherit
    the BaseResource or one of the more specific resource types like BaseAccount,
    BaseInstance, BaseNetwork, BaseLoadBalancer, etc.

    When the collect() method finishes, the Collector will retrieve the
    Plugins Graph and append it to the global Graph.
    """

    plugin_type = PluginType.COLLECTOR  # Type of the Plugin
    cloud: str = NotImplemented  # Name of the cloud this plugin implements

    def __init__(
        self,
        graph_queue: Optional[Queue[Optional[Graph]]] = None,
        graph_merge_kind: GraphMergeKind = GraphMergeKind.cloud,
        task_data: Optional[Json] = None,
        max_resources_per_account: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.name = str(self.cloud)
        cloud = Cloud(id=self.cloud)
        self.root = cloud
        self._graph_queue: Optional[Queue[Optional[Graph]]] = graph_queue
        self.graph_merge_kind: GraphMergeKind = graph_merge_kind
        self.graph = self.new_graph()
        self.task_data = task_data
        self.max_resources_per_account = max_resources_per_account

    @abstractmethod
    def collect(self) -> None:
        """Collects all the Cloud Resources"""
        pass

    @staticmethod
    def auto_enableable() -> bool:
        """Should this collector be enabled by default?"""
        pass

    @staticmethod
    def update_tag(config: Config, resource: BaseResource, key: str, value: str) -> bool:
        """Update the tag of a resource"""
        pass

    @staticmethod
    def delete_tag(config: Config, resource: BaseResource, key: str) -> bool:
        """Delete the tag of a resource"""
        pass

    @staticmethod
    def pre_cleanup(config: Config, resource: BaseResource, graph: Graph) -> bool:
        pass

    @staticmethod
    def cleanup(config: Config, resource: BaseResource, graph: Graph) -> bool:
        pass

    def go(self) -> None:
        pass

    def new_graph(self) -> Graph:
        pass

    def send_account_graph(self, graph: Graph) -> None:
        pass

    def send_graph(self, graph: Graph) -> None:
        pass
