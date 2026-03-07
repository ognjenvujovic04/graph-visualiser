"""
Defines the Node abstraction used in the graph data model.

A Node represents a single entity in the graph. Each node has a unique
identifier and a collection of attributes represented as key–value pairs.
Attributes are stored using the AttributeValue abstraction which ensures
type safety for attribute data.
"""

from typing import Dict, Optional
from .attributes import AttributeValue


class Node:
    """
    Represents a node in the graph data model.

    Nodes are created by DataSource plugins when parsing input data.
    Each node has a unique string identifier and a dictionary of
    attributes that describe the node.

    Args:
        node_id: Unique identifier of the node.
    """

    def __init__(self, node_id: str):
        """
        Initializes a new Node instance.

        Args:
            node_id: Unique identifier of the node.

        Raises:
            TypeError: If node_id is not a string.
        """
        if not isinstance(node_id, str):
            raise TypeError("Node id must be str")
        self.__id = node_id
        self.__attributes: Dict[str, AttributeValue] = {}

    @property
    def id(self) -> str:
        """
        Returns the unique identifier of the node.

        Returns:
            str: Node identifier.
        """
        return self.__id

    @property
    def attributes(self) -> Dict[str, AttributeValue]:
        """
        Returns the dictionary of node attributes.

        Returns:
            Dict[str, AttributeValue]: Mapping between attribute names
            and their corresponding values.
        """
        return self.__attributes

    def add_attribute(self, key: str, value: AttributeValue) -> None:
        """
        Adds or updates an attribute for the node.

        Args:
            key: Name of the attribute.
            value: AttributeValue instance representing the attribute value.

        Raises:
            TypeError: If key is not a string or value is not AttributeValue.
        """
        if not isinstance(key, str):
            raise TypeError("Attribute key must be str")
        if not isinstance(value, AttributeValue):
            raise TypeError("Attribute value must be AttributeValue")
        self.__attributes[key] = value

    def remove_attribute(self, key: str) -> None:
        """
        Removes an attribute from the node if it exists.

        Args:
            key: Name of the attribute to remove.
        """
        self.__attributes.pop(key, None)

    def get_attribute(self, key: str) -> Optional[AttributeValue]:
        """
        Retrieves an attribute value by key.

        Args:
            key: Name of the attribute.

        Returns:
            Optional[AttributeValue]: The attribute value if present,
            otherwise None.
        """
        return self.__attributes.get(key)

    def __str__(self) -> str:
        """
        Returns a string representation of the node.

        Returns:
            str: Formatted string containing node id and attributes.
        """
        if not self.__attributes:
            return f"Node({self.id})"
        attrs = ", ".join(f"{k}={v}" for k, v in self.__attributes.items())
        return f"Node({self.id})[{attrs}]"