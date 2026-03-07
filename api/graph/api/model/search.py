from typing import List, Optional
from .graph import Graph
from .node import Node


class SearchOperation:
    """
    Represents a search operation over a graph.

    The search operation finds nodes whose identifiers, attribute names,
    or attribute values contain the provided search text. The result of
    the operation is a new subgraph containing only the matching nodes
    and the edges that connect them.

    Search characteristics:
    - Case-insensitive matching
    - Matches node IDs
    - Matches attribute names
    - Matches attribute values
    """

    def __init__(self, search_text: str):
        """
        Initialize a search operation.

        Args:
            search_text (str): Text used to match nodes, attribute names,
                               or attribute values.

        Raises:
            TypeError: If search_text is not a string.
            ValueError: If search_text is empty or contains only whitespace.
        """
        if not isinstance(search_text, str):
            raise TypeError("search_text must be a string")
        if not search_text.strip():
            raise ValueError("search_text cannot be empty")

        self.search_text = search_text.lower()  # Case-insensitive search

    def execute(self, graph: Graph) -> Graph:
        """
        Execute the search operation on the provided graph.

        This method identifies all nodes matching the search criteria and
        constructs a new graph containing only those nodes and the edges
        that connect them.

        Args:
            graph (Graph): The graph on which the search is performed.

        Returns:
            Graph: A new graph containing only nodes that match the search
                   criteria and edges between them.

        Raises:
            TypeError: If graph is not a Graph instance.
        """
        if not isinstance(graph, Graph):
            raise TypeError("graph must be a Graph instance")

        # Find matching nodes
        matching_nodes = self._find_matching_nodes(graph)

        # Create subgraph with matching nodes
        return self._create_subgraph(graph, matching_nodes)

    def _find_matching_nodes(self, graph: Graph) -> List[Node]:
        """
        Find all nodes in the graph that match the search text.

        A node matches if:
        - its ID contains the search text, or
        - any attribute name contains the search text, or
        - any attribute value contains the search text.

        Args:
            graph (Graph): Graph to search.

        Returns:
            List[Node]: List of nodes that satisfy the search criteria.
        """
        matching_nodes = []

        for node in graph.nodes:
            # Check if node ID contains search text
            if self.search_text in node.id.lower():
                matching_nodes.append(node)
                continue

            # Check if any attribute name or value contains search text
            if self._node_has_matching_attribute(node):
                matching_nodes.append(node)

        return matching_nodes

    def _node_has_matching_attribute(self, node: Node) -> bool:
        """
        Check whether a node contains an attribute that matches the search text.

        The method checks both attribute names and attribute values.

        Args:
            node (Node): Node to inspect.

        Returns:
            bool: True if at least one attribute name or value matches
                  the search text, otherwise False.
        """
        for attr_name, attr_value in node.attributes.items():
            # Check attribute name
            if self.search_text in attr_name.lower():
                return True

            # Check attribute value (convert to string for comparison)
            attr_value_str = str(attr_value).lower()
            if self.search_text in attr_value_str:
                return True

        return False

    def _create_subgraph(self, original_graph: Graph, matching_nodes: List[Node]) -> Graph:
        """
        Construct a subgraph containing only the matching nodes.

        The new graph preserves the structural properties of the original
        graph (directed/undirected and cyclic/acyclic). Nodes are copied
        to avoid modifying the original graph. Only edges whose source and
        target are both in the matching node set are included.

        Args:
            original_graph (Graph): The original graph.
            matching_nodes (List[Node]): Nodes that matched the search criteria.

        Returns:
            Graph: A newly constructed subgraph containing the matching nodes
                   and their connecting edges.
        """
        # Create new graph with same properties as original
        subgraph = Graph(directed=original_graph.directed, cyclic=original_graph.cyclic)

        # Create mapping of node IDs for easy lookup
        matching_node_ids = {node.id for node in matching_nodes}

        # Add all matching nodes to subgraph
        for node in matching_nodes:
            # Create a copy of the node to avoid modifying original
            node_copy = Node(node.id)
            for attr_name, attr_value in node.attributes.items():
                node_copy.add_attribute(attr_name, attr_value)
            subgraph.add_node(node_copy)

        # Add edges that connect nodes in the subgraph
        for edge in original_graph.edges:
            if edge.source.id in matching_node_ids and edge.target.id in matching_node_ids:
                source_node = subgraph.get_node(edge.source.id)
                target_node = subgraph.get_node(edge.target.id)
                if source_node and target_node:
                    subgraph.add_edge(source_node, target_node, edge.label)

        return subgraph

    def __str__(self) -> str:
        """
        Return a human-readable representation of the search operation.
        """
        return f"SearchOperation('{self.search_text}')"

    def __repr__(self) -> str:
        """
        Return a detailed representation of the search operation.
        """
        return f"SearchOperation(search_text='{self.search_text}')"
