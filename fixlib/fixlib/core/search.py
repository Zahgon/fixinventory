import json
from typing import Optional, Iterator, Dict, Any
from urllib.parse import urlencode

import requests

from fixlib.args import ArgumentParser
from fixlib.baseresources import EdgeType
from fixlib.config import Config
from fixlib.core import fixcore
from fixlib.core.ca import TLSData
from fixlib.core.model_export import node_from_dict, node_to_dict
from fixlib.graph import Graph, sanitize
from fixlib.jwt import encode_jwt_to_headers
from fixlib.logger import log
from fixlib.types import Json


class CoreGraph:
    def __init__(
        self,
        base_uri: Optional[str] = None,
        graph: Optional[str] = None,
        tls_data: Optional[TLSData] = None,
    ) -> None:
        if base_uri is None:
            self.base_uri = fixcore.http_uri
        else:
            self.base_uri = base_uri.strip("/")
        if graph is None:
            self.graph_name = Config.fixworker.graph
        else:
            self.graph_name = graph
        self.verify = None
        if tls_data:
            self.verify = tls_data.ca_cert_path
        self.graph_uri = f"{self.base_uri}/graph/{self.graph_name}"
        self.search_uri = f"{self.graph_uri}/search/graph"

    def execute(self, command: str) -> Iterator[Json]:
        log.debug(f"Executing command: {command}")
        headers = {"Accept": "application/x-ndjson", "Content-Type": "text/plain"}
        execute_endpoint = f"{self.base_uri}/cli/execute"
        if self.graph_name:
            query_string = urlencode({"graph": self.graph_name})
            execute_endpoint += f"?{query_string}"
        return self.post(execute_endpoint, command, headers, verify=self.verify)

    def search(self, search: str, edge_type: Optional[EdgeType] = None, section: str = "reported") -> Iterator[Json]:
        pass

    @staticmethod
    def post(uri: str, data: str, headers: Dict[str, str], verify: Optional[str] = None) -> Iterator[Json]:
        if getattr(ArgumentParser.args, "psk", None):
            encode_jwt_to_headers(headers, {}, ArgumentParser.args.psk)
        r = requests.post(uri, data=data, headers=headers, stream=True, verify=verify)
        if r.status_code != 200:
            log.error(r.content.decode())
            raise RuntimeError(f"Failed to search graph: {r.content.decode()}")
        for line in r.iter_lines():
            if not line:
                continue
            try:
                response: Json = json.loads(line.decode("utf-8"))
                yield response
            except TypeError as e:
                log.error(e)
                continue

    def graph(self, search: str) -> Graph:
        pass

    def patch_nodes(self, graph: Graph) -> None:
        pass


class GraphChangeIterator:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def __iter__(self) -> Iterator[bytes]:
        for node in self.graph.nodes:
            if not node.changes.changed:
                continue
            node_dict = node_to_dict(node, changes_only=True)
            node_json = json.dumps(node_dict) + "\n"
            log.debug(f"Updating node {node_dict}")
            yield node_json.encode()
