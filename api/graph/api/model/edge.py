from typing import Dict
from .attributes import AttributeValue
from .node import Node


class Edge:
    def __init__(self, edge_id: str, source: Node, target: Node, label: str = ""):
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
        return self.__id

    @property
    def source(self) -> Node:
        return self.__source

    @property
    def target(self) -> Node:
        return self.__target

    @property
    def label(self) -> str:
        return self.__label

    @property
    def attributes(self) -> Dict[str, AttributeValue]:
        return self.__attributes

    def add_attribute(self, key: str, value: AttributeValue) -> None:
        if not isinstance(key, str):
            raise TypeError("Attribute key must be str")
        if not isinstance(value, AttributeValue):
            raise TypeError("Value must be AttributeValue")
        self.__attributes[key] = value

    def __str__(self) -> str:
        lab = f", label='{self.__label}'" if self.__label else ""
        return f"Edge({self.__source.id} -> {self.__target.id}{lab})"