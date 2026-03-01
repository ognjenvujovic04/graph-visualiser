from typing import Dict, List, Optional
from .node import Node
from .edge import Edge
from collections import deque

class Graph:
    def __init__(self, directed: bool = True, cyclic: bool = True):
        self.__nodes: Dict[str, Node] = {}
        self.__edges: Dict[str, Edge] = {}
        self.__edge_counter = 0

        self.directed = directed
        self.cyclic = cyclic

    @property
    def directed(self) -> bool:
        return self.__directed

    @directed.setter
    def directed(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("directed must be bool")
        self.__directed = value

    @property
    def cyclic(self) -> bool:
        return self.__cyclic

    @cyclic.setter
    def cyclic(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("cyclic must be bool")
        self.__cyclic = value

    @property
    def nodes(self) -> List[Node]:
        return list(self.__nodes.values())

    def add_node(self, node: Node) -> None:
        if not isinstance(node, Node):
            raise TypeError("Must be Node")
        if node.id in self.__nodes:
            raise ValueError("Node already exists")
        self.__nodes[node.id] = node

    def remove_node(self, node: Node) -> None:
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
        return self.__nodes.get(node_id)

    @property
    def edges(self) -> List[Edge]:
        return list(self.__edges.values())

    def add_edge(self, source: Node, target: Node, label: str = "") -> Edge:
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
        if not isinstance(edge, Edge):
            raise TypeError("Must be Edge")
        self.__edges.pop(edge.id, None)

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        return self.__edges.get(edge_id)

    def __neighbors(self, node: Node) -> List[Node]:
        result: List[Node] = []
        for e in self.__edges.values():
            if e.source.id == node.id:
                result.append(e.target)
        return result

    def __would_create_cycle(self, source: Node, target: Node) -> bool:
        return self.__path_exists(target, source)

    def __path_exists(self, start: Node, goal: Node) -> bool:
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


    def __str__(self) -> str:
        d = "directed" if self.__directed else "undirected"
        c = "cyclic" if self.__cyclic else "acyclic"
        return f"Graph({d}, {c}, nodes={len(self.__nodes)}, edges={len(self.__edges)})"
    
    def print_bfs(self, start: Node) -> None:
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