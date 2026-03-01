from typing import Dict, Optional
from .attributes import AttributeValue

class Node:
    def __init__(self, node_id: str):
        if not isinstance(node_id, str):
            raise TypeError("Node id must be str")
        self.__id = node_id
        self.__attributes: Dict[str, AttributeValue] = {}

    @property
    def id(self) -> str:
        return self.__id

    @property
    def attributes(self) -> Dict[str, AttributeValue]:
        return self.__attributes

    def add_attribute(self, key: str, value: AttributeValue) -> None:
        if not isinstance(key, str):
            raise TypeError("Attribute key must be str")
        if not isinstance(value, AttributeValue):
            raise TypeError("Attribute value must be AttributeValue")
        self.__attributes[key] = value

    def remove_attribute(self, key: str) -> None:
        self.__attributes.pop(key, None)

    def get_attribute(self, key: str) -> Optional[AttributeValue]:
        return self.__attributes.get(key)

    def __str__(self) -> str:
        if not self.__attributes:
            return f"Node({self.id})"
        attrs = ", ".join(f"{k}={v}" for k, v in self.__attributes.items())
        return f"Node({self.id})[{attrs}]"