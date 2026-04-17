from __future__ import annotations

from abc import abstractmethod, ABC
from typing import List, Optional, Any, Dict, Callable

from attr import define, field, evolve
from fixlib.tree import Tree, Node

from fixlib.types import Json, JsonElement

_TreeRoot = "root"


@define
class ProgressInfo:
    current: int
    total: int

    @property
    def percentage(self) -> int:
        pass

    @property
    def done(self) -> bool:
        pass


@define
class Progress(ABC):
    name: str
    path: List[str] = field(kw_only=True, factory=list)

    @abstractmethod
    def overall_progress(self) -> ProgressInfo:
        pass

    @abstractmethod
    def update_progress(self, progress: Progress) -> Progress:
        pass

    @abstractmethod
    def mark_done(self) -> Progress:
        pass

    @property
    def percentage(self) -> int:
        pass

    @staticmethod
    def from_progresses(name: str, progresses: List[Progress]) -> ProgressTree:
        pass

    def to_json(self, key: Optional[Callable[[Progress], Any]] = None) -> Json:
        p = {"path": self.path} if self.path else {}
        if isinstance(self, ProgressDone):
            return {
                "kind": "progress",
                "name": self.name,
                **p,
                "current": self.current,
                "total": self.total,
            }
        elif isinstance(self, ProgressTree):
            node_iter = (part.data for part in self.sub_tree.all_nodes_itr() if part.data is not None)
            nodes: List[Progress] = sorted(node_iter, key=key) if key else list(node_iter)
            return {"kind": "tree", "name": self.name, **p, "parts": [part.to_json() for part in nodes]}
        else:
            raise AttributeError("No handler to marshal progress")

    def info_json(self) -> JsonElement:
        pass

    @staticmethod
    def from_json(json: Json) -> Progress:
        name = json["name"]
        path = json.get("path", [])
        if json["kind"] == "progress":
            return ProgressDone(name, json["current"], json["total"], path=path)
        elif json["kind"] == "tree":
            tree = ProgressTree(name, path=path)
            for part in json["parts"]:
                tree.add_progress(Progress.from_json(part))
            return tree
        else:
            raise AttributeError("No handler to unmarshal progress")


@define
class ProgressDone(Progress):
    current: int
    total: int

    def __attrs_post_init__(self) -> None:
        if self.total <= 0:
            raise ValueError("total must be greater than 0")
        if self.current > self.total:
            raise ValueError(f"current ({self.current}) > total ({self.total})")

    def __str__(self) -> str:
        return f"{self.current}/{self.total}"

    def overall_progress(self) -> ProgressInfo:
        pass

    def update_progress(self, progress: Progress) -> Progress:
        pass

    def mark_done(self) -> Progress:
        pass


@define(eq=False)
class ProgressTree(Progress):
    sub_tree: Tree = field(factory=Tree)

    def __attrs_post_init__(self) -> None:
        if not self.sub_tree.root:
            self.sub_tree.create_node(_TreeRoot, _TreeRoot)

    def __eq__(self, other: Any) -> bool:
        def data_nodes(tree: Tree) -> Dict[str, Progress]:
            pass

        if isinstance(other, ProgressTree):
            return data_nodes(self.sub_tree) == data_nodes(other.sub_tree)
        else:
            return False

    def sub_progress(self, nid: str) -> Optional[Progress]:
        pass

    def has_path(self, nid: str) -> bool:
        pass

    def by_path(self, nid: str) -> Optional[Progress]:
        pass

    def overall_progress(self) -> ProgressInfo:
        pass

    def mark_done(self) -> Progress:
        pass

    def update_progress(self, progress: Progress) -> Progress:
        pass

    def add_progress(self, progress: Progress) -> None:
        last: str = self.sub_tree.root  # type: ignore
        last_path = last
        path = last
        for part in progress.path:
            path += "." + part
            if path not in self.sub_tree:  # if the path does not exist, create it
                self.sub_tree.create_node(part, path, parent=last_path)
            elif self.sub_tree[path].data is not None:  # if the path contains a value: remove it
                self.sub_tree[path].data = None
            last_path = path

        nid = path + "." + progress.name
        if nid in self.sub_tree and nid != self.sub_tree.root:
            self.sub_tree.remove_node(nid)
        if isinstance(progress, ProgressDone):
            self.sub_tree.create_node(progress.name, nid, parent=last_path, data=progress)
        elif isinstance(progress, ProgressTree):
            rp = nid.split(".")[1:]  # the relative path of the progress tree inside current tree (without root)
            for node in progress.sub_tree.leaves():
                if data := node.data:
                    np = node.identifier.split(".")[1:-1]  # relative path of leaf: no root not current node
                    self.add_progress(evolve(data, path=rp + np + data.path))

    def copy(self) -> ProgressTree:
        return evolve(self, sub_tree=Tree(self.sub_tree.subtree(self.sub_tree.root), deep=True))
