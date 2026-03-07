"""
Defines the Edge abstraction used in the graph data model.

An Edge represents a connection between two nodes in the graph. Each edge
has a unique identifier, a source node, a target node, and an optional label.
Edges may also contain additional attributes represented using the
AttributeValue abstraction.
"""

from typing import Dict
from .attributes import AttributeValue
from .node import Node


class Edge:
    """
    Represents an edge in the graph data model.

    An edge connects two nodes (source and target) and may optionally
    have a label describing the relationship between them. Edges can
    also store additional attributes using key–value pairs.

    Args:
        edge_id: Unique identifier of the edge.
        source: Source node of the edge.
        target: Target node of the edge.
        label: Optional textual label describing the relationship.
    """

    def __init__(self, edge_id: str, source: Node, target: Node, label: str = ""):
        """
        Initializes a new Edge instance.

        Args:
            edge_id: Unique identifier of the edge.
            source: Node where the edge originates.
            target: Node where the edge points.
            label: Optional label describing the relationship.

        Raises:
            TypeError: If any of the provided arguments have invalid types.
        """
        if not isinstance(edge_id, str):
            raise TypeError("Edge id must be str")
        if not isinstance(source, Node):
            raise TypeError("Source must be Node")
        if not isinstance(target, Node):
            raise TypeError("Target must be Node")
        if not isinstance(label, str):
            raise TypeError("Label must be str")

        self.__id = edge_id
        self.__source = source
        self.__target = target
        self.__label = label
        self.__attributes: Dict[str, AttributeValue] = {}

    @property
    def id(self) -> str:
        """
        Returns the unique identifier of the edge.

        Returns:
            str: Edge identifier.
        """
        return self.__id

    @property
    def source(self) -> Node:
        """
        Returns the source node of the edge.

        Returns:
            Node: Node where the edge originates.
        """
        return self.__source

    @property
    def target(self) -> Node:
        """
        Returns the target node of the edge.

        Returns:
            Node: Node where the edge points.
        """
        return self.__target

    @property
    def label(self) -> str:
        """
        Returns the label describing the edge relationship.

        Returns:
            str: Edge label.
        """
        return self.__label

    @property
    def attributes(self) -> Dict[str, AttributeValue]:
        """
        Returns the dictionary of edge attributes.

        Returns:
            Dict[str, AttributeValue]: Mapping between attribute names
            and their corresponding values.
        """
        return self.__attributes

    def add_attribute(self, key: str, value: AttributeValue) -> None:
        """
        Adds or updates an attribute for the edge.

        Args:
            key: Name of the attribute.
            value: AttributeValue instance representing the attribute value.

        Raises:
            TypeError: If key is not a string or value is not AttributeValue.
        """
        if not isinstance(key, str):
            raise TypeError("Attribute key must be str")
        if not isinstance(value, AttributeValue):
            raise TypeError("Value must be AttributeValue")
        self.__attributes[key] = value

    def __str__(self) -> str:
        """
        Returns a string representation of the edge.

        Returns:
            str: Formatted string showing the connection between nodes
            and an optional label.
        """
        lab = f", label='{self.__label}'" if self.__label else ""
        return f"Edge({self.__source.id} -> {self.__target.id}{lab})"