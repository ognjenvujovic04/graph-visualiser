from abc import ABC, abstractmethod
from graph.api.model.graph import Node, Edge, Graph


class Builder(ABC):
    """
    Abstract builder interface for constructing graph domain objects.

    Builder implementations are responsible for creating instances of
    Node, Edge, and Graph objects from external data representations.
    This abstraction allows different data source plugins or parsers
    to construct graph structures in a consistent way.
    """

    @abstractmethod
    def build_node(self, attribute: dict) -> Node:
        """
        Create a Node instance from a dictionary of attributes.

        Implementations should interpret the provided attribute dictionary
        and populate the resulting node with appropriate attribute values.

        Args:
            attribute (dict): Dictionary containing node attribute data.

        Returns:
            Node: Constructed node instance.
        """
        pass

    @abstractmethod
    def build_edge(self, source: Node, target: Node, label: str) -> Edge:
        """
        Create an Edge instance connecting two nodes.

        Args:
            source (Node): Source node of the edge.
            target (Node): Target node of the edge.
            label (str): Label associated with the edge.

        Returns:
            Edge: Constructed edge instance.
        """
        pass

    @abstractmethod
    def build_graph(self, directed: bool, cyclic: bool, nodes: list[Node], edges: list[Edge]) -> Graph:
        """
        Construct a Graph instance from nodes and edges.

        Args:
            directed (bool): Indicates whether the graph is directed.
            cyclic (bool): Indicates whether the graph allows cycles.
            nodes (list[Node]): List of nodes to include in the graph.
            edges (list[Edge]): List of edges to include in the graph.

        Returns:
            Graph: Constructed graph instance.
        """
        pass