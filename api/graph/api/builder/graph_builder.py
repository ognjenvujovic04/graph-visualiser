from datetime import datetime
from typing import Any

from graph.api.model.attributes import AttributeValue, AttributeType
from graph.api.model.graph import Node,Edge, Graph
from graph.api.builder.builder import Builder


class GraphBuilder(Builder):
    def __init__(self):
        self.__graph = None

    def build_node(self, attributes: dict, id_key: str = "id") -> Node:
        node = Node(attributes[id_key])
        for key, value in attributes.items():
            if key == id_key or isinstance(value, (dict, list)):
                continue
            node.add_attribute(key, self.__to_attr_value(value))
        self.__graph.add_node(node)
        return node

    def __to_attr_value(self, v: Any) -> AttributeValue:
        if v is None or isinstance(v, bool):
            return AttributeValue(AttributeType.STR, str(v))

        if isinstance(v, int):
            return AttributeValue(AttributeType.INT, v)

        if isinstance(v, float):
            return AttributeValue(AttributeType.FLOAT, v)

        if isinstance(v, str):
            s = v.strip()
            if s == "":
                return AttributeValue(AttributeType.STR, "")

            if len(s) == 10 and s[4] == "-" and s[7] == "-":
                try:
                    d = datetime.strptime(s, "%Y-%m-%d")
                    return AttributeValue(AttributeType.DATE, d)
                except ValueError:
                    pass

            try:
                return AttributeValue(AttributeType.INT, int(s))
            except ValueError:
                pass
            try:
                return AttributeValue(AttributeType.FLOAT, float(s))
            except ValueError:
                pass
            return AttributeValue(AttributeType.STR, v)

        return AttributeValue(AttributeType.STR, str(v))

    def build_edge(self, source:Node,target:Node,label:str) ->Edge:
        return self.__graph.add_edge(source, target, label)

    def build_graph(self, directed: bool, cyclic: bool) -> Graph:
        self.__graph = Graph(directed=directed, cyclic=cyclic)
        return self.__graph

    def update_node(self, node: Node, attributes: dict, id_key: str = "id", ref_key: str = None) -> None:
        for key, value in attributes.items():
            if key not in (id_key, ref_key) and not isinstance(value, (dict, list)):
                node.add_attribute(key, self.__to_attr_value(value))

