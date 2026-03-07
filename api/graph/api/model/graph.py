"""
Graph module defining the central graph data structure used by the platform.

The Graph class represents a collection of nodes and edges and serves as the
core data model exchanged between DataSource plugins, the platform, and
Visualizer plugins. It supports directed or undirected graphs and optional
cycle constraints, as well as search, filter and traversal operations.
"""

from typing import Dict, List, Optional, TYPE_CHECKING
from .node import Node
from .edge import Edge
from collections import deque

if TYPE_CHECKING:
    from .search import SearchOperation
    from .filter import FilterOperation


class Graph:
    """
    Represents a graph consisting of nodes and edges.

    The graph stores nodes indexed by their identifier and edges connecting
    those nodes. It supports both directed and undirected graphs and can
    optionally prevent cycles.
    """

    def __init__(self, directed: bool = True, cyclic: bool = True):
        """
        Initializes a new Graph instance.

        Args:
            directed: If True, the graph is directed.
            cyclic: If False, the graph will reject edges that introduce cycles.
        """
        self.__nodes: Dict[str, Node] = {}
        self.__edges: Dict[str, Edge] = {}
        self.__edge_counter = 0

        self.directed = directed
        self.cyclic = cyclic

    @property
    def directed(self) -> bool:
        """
        Indicates whether the graph is directed.

        Returns:
            bool: True if the graph is directed.
        """
        return self.__directed

    @directed.setter
    def directed(self, value: bool) -> None:
        """
        Sets whether the graph is directed.

        Args:
            value: Boolean indicating directed behavior.

        Raises:
            TypeError: If value is not bool.
        """
        if not isinstance(value, bool):
            raise TypeError("directed must be bool")
        self.__directed = value

    @property
    def cyclic(self) -> bool:
        """
        Indicates whether cycles are allowed in the graph.

        Returns:
            bool: True if cycles are allowed.
        """
        return self.__cyclic

    @cyclic.setter
    def cyclic(self, value: bool) -> None:
        """
        Sets whether cycles are allowed in the graph.

        Args:
            value: Boolean indicating cyclic behavior.

        Raises:
            TypeError: If value is not bool.
        """
        if not isinstance(value, bool):
            raise TypeError("cyclic must be bool")
        self.__cyclic = value

    @property
    def nodes(self) -> List[Node]:
        """
        Returns all nodes contained in the graph.

        Returns:
            List[Node]: List of graph nodes.
        """
        return list(self.__nodes.values())

    def add_node(self, node: Node) -> None:
        """
        Adds a node to the graph.

        Args:
            node: Node instance to add.

        Raises:
            TypeError: If the argument is not a Node.
            ValueError: If a node with the same id already exists.
        """
        if not isinstance(node, Node):
            raise TypeError("Must be Node")
        if node.id in self.__nodes:
            raise ValueError("Node already exists")
        self.__nodes[node.id] = node

    def remove_node(self, node: Node) -> None:
        """
        Removes a node from the graph.

        A node cannot be removed if there are edges connected to it.

        Args:
            node: Node instance to remove.

        Raises:
            TypeError: If node is not Node.
            ValueError: If node has connected edges.
        """
        if not isinstance(node, Node):
            raise TypeError("Must be Node")
        if node.id not in self.__nodes:
            return

        # ne dozvoli brisanje ako postoje povezane grane
        for e in self.__edges.values():
            if e.source.id == node.id or e.target.id == node.id:
                raise ValueError("Cannot delete node with connected edges")

        del self.__nodes[node.id]

    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Retrieves a node by its identifier.

        Args:
            node_id: Node identifier.

        Returns:
            Optional[Node]: The node if it exists, otherwise None.
        """
        return self.__nodes.get(node_id)

    @property
    def edges(self) -> List[Edge]:
        """
        Returns all edges contained in the graph.

        Returns:
            List[Edge]: List of graph edges.
        """
        return list(self.__edges.values())

    def add_edge(self, source: Node, target: Node, label: str = "") -> Edge:
        """
        Creates and adds a new edge between two nodes.

        Args:
            source: Source node.
            target: Target node.
            label: Optional label describing the relationship.

        Returns:
            Edge: The created edge.

        Raises:
            TypeError: If source or target are not Node.
            ValueError: If nodes are not part of the graph or a cycle would be created.
        """
        if not isinstance(source, Node) or not isinstance(target, Node):
            raise TypeError("source/target must be Node")

        # provera da su nodovi iz ovog grafa (po id-u)
        if source.id not in self.__nodes or target.id not in self.__nodes:
            raise ValueError("Both nodes must be added to graph before creating an edge")

        # ako graf nije ciklican, zabrani granu koja pravi ciklus
        if not self.__cyclic and self.__would_create_cycle(source, target):
            raise ValueError("Edge would create a cycle (graph is acyclic)")

        self.__edge_counter += 1
        edge_id = f"e{self.__edge_counter}"
        edge = Edge(edge_id, source, target, label)
        self.__edges[edge_id] = edge

        # ako je neusmeren graf, dodaj i kontra-granu
        if not self.__directed and source.id != target.id:
            self.__edge_counter += 1
            edge_id2 = f"e{self.__edge_counter}"
            edge2 = Edge(edge_id2, target, source, label)
            self.__edges[edge_id2] = edge2

        return edge

    def remove_edge(self, edge: Edge) -> None:
        """
        Removes an edge from the graph.

        Args:
            edge: Edge instance to remove.

        Raises:
            TypeError: If edge is not Edge.
        """
        if not isinstance(edge, Edge):
            raise TypeError("Must be Edge")
        self.__edges.pop(edge.id, None)

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """
        Retrieves an edge by its identifier.

        Args:
            edge_id: Edge identifier.

        Returns:
            Optional[Edge]: The edge if it exists, otherwise None.
        """
        return self.__edges.get(edge_id)

    def __neighbors(self, node: Node) -> List[Node]:
        """
        Returns neighboring nodes reachable from the given node.

        Args:
            node: Node whose neighbors should be retrieved.

        Returns:
            List[Node]: List of adjacent nodes.
        """
        result: List[Node] = []
        for e in self.__edges.values():
            if e.source.id == node.id:
                result.append(e.target)
        return result

    def __would_create_cycle(self, source: Node, target: Node) -> bool:
        """
        Checks whether adding an edge would introduce a cycle.

        Args:
            source: Source node of the potential edge.
            target: Target node of the potential edge.

        Returns:
            bool: True if the edge would create a cycle.
        """
        return self.__path_exists(target, source)

    def __path_exists(self, start: Node, goal: Node) -> bool:
        """
        Determines whether a path exists between two nodes.

        Args:
            start: Starting node.
            goal: Destination node.

        Returns:
            bool: True if a path exists between the nodes.
        """
        if start.id == goal.id:
            return True

        visited = set()
        stack = [start]

        while stack:
            current = stack.pop()
            if current.id == goal.id:
                return True
            if current.id in visited:
                continue
            visited.add(current.id)

            for n in self.__neighbors(current):
                if n.id not in visited:
                    stack.append(n)

        return False

    def has_cycle(self) -> bool:
        """
        Detects whether the graph contains a cycle.

        Returns:
            bool: True if a cycle exists.
        """
        visited = set()
        stack = set()

        def dfs(node):
            if node.id in stack:
                return True
            if node.id in visited:
                return False

            visited.add(node.id)
            stack.add(node.id)

            for n in self.__neighbors(node):
                if dfs(n):
                    return True

            stack.remove(node.id)
            return False

        for node in self.nodes:
            if dfs(node):
                return True

        return False

    def search(self, search_text: str) -> 'Graph':
        """
        Executes a search operation over the graph.

        Args:
            search_text: Text used for searching within node attributes.

        Returns:
            Graph: Graph containing search results.
        """
        from .search import SearchOperation

        search_op = SearchOperation(search_text)
        return search_op.execute(self)

    def filter(self, filter_expr) -> 'Graph':
        """
        Executes a filter operation over the graph.

        Args:
            filter_expr: Filtering expression.

        Returns:
            Graph: Graph containing filtered results.
        """
        from .filter import FilterOperation

        filter_op = FilterOperation(filter_expr)
        return filter_op.execute(self)

    def __str__(self) -> str:
        """
        Returns a textual summary of the graph.

        Returns:
            str: Description of graph type and size.
        """
        d = "directed" if self.__directed else "undirected"
        c = "cyclic" if self.__cyclic else "acyclic"
        return f"Graph({d}, {c}, nodes={len(self.__nodes)}, edges={len(self.__edges)})"

    def print_bfs(self, start: Node) -> None:
        """
        Performs a BFS traversal and prints visited edges.

        Args:
            start: Starting node of the traversal.

        Raises:
            TypeError: If start is not Node.
            ValueError: If the node is not part of the graph.
        """
        if not isinstance(start, Node):
            raise TypeError("start must be Node")
        if start.id not in self.__nodes:
            raise ValueError("Start node not in graph")

        def fmt(n: Node) -> str:
            if not n.attributes:
                return f"{n.id}{{}}"
            attrs = ", ".join(f"{k}={v.value}" for k, v in n.attributes.items())
            return f"{n.id}{{{attrs}}}"

        visited = set([start.id])
        queue = deque([start])

        printed_pairs = set()  # samo za undirected da ne stampamo A-B i B-A

        print(f"\nBFS starting from {fmt(start)}:\n")

        while queue:
            current = queue.popleft()

            for edge in self.__edges.values():
                if edge.source.id != current.id:
                    continue

                if not self.__directed:
                    pair = frozenset([edge.source.id, edge.target.id])
                    if pair in printed_pairs:
                        continue
                    printed_pairs.add(pair)

                arrow = "-->" if self.__directed else "--"
                print(f"{fmt(edge.source)} --({edge.id}){arrow} {fmt(edge.target)}")

                if edge.target.id not in visited:
                    visited.add(edge.target.id)
                    queue.append(edge.target)