from datetime import datetime
from typing import Any

from graph.api.model.attributes import AttributeValue, AttributeType
from graph.api.model.graph import Node,Edge, Graph
from graph.api.builder.builder import Builder


class GraphBuilder(Builder):
    """
    Concrete builder implementation for constructing Graph domain objects.

    GraphBuilder is responsible for incrementally creating nodes and edges
    and assembling them into a Graph instance. It also performs conversion
    of raw attribute values into AttributeValue objects used by the domain
    model.

    This builder is typically used by data source plugins or parsers when
    transforming external data (e.g. JSON, XML) into the internal graph model.
    """

    def __init__(self):
        """
        Initialize the builder.

        The builder maintains an internal Graph instance that is populated
        during the building process.
        """
        self.__graph = None

    def build_node(self, attributes: dict, id_key: str = "id") -> Node:
        """
        Create and add a Node to the current graph.

        The node identifier is taken from the provided attribute dictionary
        using the specified id_key. Other primitive attribute values are
        converted to AttributeValue instances and attached to the node.

        Nested structures such as dictionaries or lists are ignored.

        Args:
            attributes (dict): Dictionary containing node attributes.
            id_key (str): Key used to extract the node identifier.

        Returns:
            Node: The constructed node that has been added to the graph.
        """
        node = Node(attributes[id_key])
        for key, value in attributes.items():
            if key == id_key or isinstance(value, (dict, list)):
                continue
            node.add_attribute(key, self.__to_attr_value(value))
        self.__graph.add_node(node)
        return node

    def __to_attr_value(self, v: Any) -> AttributeValue:
        """
        Convert a raw value into an AttributeValue instance.

        The method attempts to infer the correct attribute type using
        the following rules:

        - None and boolean values are converted to strings.
        - Integers and floats retain their numeric types.
        - Strings are checked for:
            - ISO date format (YYYY-MM-DD)
            - numeric values (int or float)
            - otherwise treated as strings.

        Args:
            v (Any): Raw attribute value.

        Returns:
            AttributeValue: Converted attribute value compatible with
                            the graph domain model.
        """
        # bool/null -> string
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
        """
        Create an edge between two nodes in the current graph.

        Args:
            source (Node): Source node.
            target (Node): Target node.
            label (str): Edge label.

        Returns:
            Edge: The created edge instance.
        """
        return self.__graph.add_edge(source, target, label)

    def build_graph(self, directed: bool, cyclic: bool) -> Graph:
        """
        Initialize and return a new Graph instance.

        This method prepares the internal graph that will be populated
        with nodes and edges during the build process.

        Args:
            directed (bool): Indicates whether the graph is directed.
            cyclic (bool): Indicates whether the graph allows cycles.

        Returns:
            Graph: Newly created graph instance.
        """
        self.__graph = Graph(directed=directed, cyclic=cyclic)
        return self.__graph

    def update_node(self, node: Node, attributes: dict, id_key: str = "id", ref_key: str = None) -> None:
        """
        Update attributes of an existing node.

        Attributes that correspond to the identifier key or reference key
        are ignored. Nested structures such as dictionaries or lists are
        also ignored.

        Args:
            node (Node): Node to update.
            attributes (dict): Dictionary containing updated attribute values.
            id_key (str): Key used for node identifiers.
            ref_key (str, optional): Key used for reference attributes
                                     that should not be added to the node.
        """
        for key, value in attributes.items():
            if key not in (id_key, ref_key) and not isinstance(value, (dict, list)):
                node.add_attribute(key, self.__to_attr_value(value))

