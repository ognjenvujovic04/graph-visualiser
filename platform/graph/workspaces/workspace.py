from typing import List, Optional
from copy import deepcopy
from graph.api.model.graph import Graph
from graph.api.services.plugin import DataSourcePlugin


class Workspace:
    """
    Predstavlja jedan workspace: plugin izvora podataka + graf + aktivni graf + istorija filtera/pretraga.
    """
    def __init__(self, name: str, source_plugin: DataSourcePlugin, graph: Graph):
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not isinstance(source_plugin, DataSourcePlugin):
            raise TypeError("source_plugin must be DataSourcePlugin")
        if not isinstance(graph, Graph):
            raise TypeError("graph must be a Graph instance")

        self.name: str = name
        self.source_plugin: DataSourcePlugin = source_plugin
        self.graph: Graph = graph  # originalni graf
        self.active_graph: Graph = deepcopy(graph)  # graf koji ide ka visualizer-u
        self.filters_history: List[str] = []
        self.search_history: List[str] = []

    def apply_filter(self, filter_expr) -> None:
        self.active_graph = self.active_graph.filter(filter_expr)
        self.filters_history.append(str(filter_expr))

    def apply_search(self, search_text: str) -> None:
        self.active_graph = self.active_graph.search(search_text)
        self.search_history.append(search_text)

    def reset_active_graph(self) -> None:
        self.active_graph = deepcopy(self.graph)
        self.filters_history.clear()
        self.search_history.clear()

    def get_active_graph(self) -> Graph:
        return self.active_graph

    def __str__(self):
        return (
            f"Workspace(name='{self.name}', plugin='{self.source_plugin.identifier()}', "
            f"nodes={len(self.active_graph.nodes)}, edges={len(self.active_graph.edges)})"
        )