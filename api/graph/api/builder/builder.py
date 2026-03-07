from abc import ABC, abstractmethod
from graph.api.model.graph import Node, Edge, Graph


class Builder(ABC):
    @abstractmethod
    def build_node(self, attribute: dict) -> Node:
        pass

    @abstractmethod
    def build_edge(self, source: Node, target: Node, label: str) -> Edge:
        pass

    @abstractmethod
    def build_graph(self, directed: bool, cyclic: bool, nodes: list[Node], edges: list[Edge]) -> Graph:
        pass