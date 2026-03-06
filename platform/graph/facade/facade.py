from typing import Optional
import copy

from graph.api.model.graph import Graph
from graph.api.model.node import Node
from graph.api.model.edge import Edge
from graph.api.model.attributes import AttributeValue, AttributeType
from graph.use_cases.plugin_recognition import PluginRegistry
from graph.factory.data_source_factory import DataSourceFactory
from graph.factory.visualizer_factory import VisualizerFactory


class PlatformFacade:
    """
    Single entry point for all platform operations.
    Django, Flask and CLI all go through this class exclusively.
    Implemented as a Singleton.
    """

    _instance: Optional['PlatformFacade'] = None

    def __new__(cls) -> 'PlatformFacade':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._registry = PluginRegistry()
        self._registry.load_all()

        self._ds_factory = DataSourceFactory(self._registry)
        self._viz_factory = VisualizerFactory(self._registry)

        self._active_graph: Optional[Graph] = None
        self._original_graph: Optional[Graph] = None  # for reset

    # ------------------------------------------------------------------
    # Singleton access
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> 'PlatformFacade':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Plugin info
    # ------------------------------------------------------------------

    def get_datasources(self) -> list:
        """Return list of available datasource plugins."""
        return self._registry.datasources

    def get_visualizers(self) -> list:
        """Return list of available visualizer plugins."""
        return self._registry.visualizers

    # ------------------------------------------------------------------
    # Graph loading
    # ------------------------------------------------------------------

    def load_graph(self, plugin_id: str, **kwargs) -> Graph:
        """
        Load a graph using the specified datasource plugin.
        The loaded graph becomes the active graph.

        Args:
            plugin_id: identifier of the datasource plugin (e.g. 'json', 'csv')
            **kwargs:  plugin-specific args (e.g. path='file.json', direct='y')

        Returns:
            The loaded Graph
        """
        plugin = self._ds_factory.create_plugin(plugin_id)
        graph = plugin.load(**kwargs)

        self._original_graph = copy.deepcopy(graph)
        self._active_graph = graph
        return graph

    def get_active_graph(self) -> Optional[Graph]:
        """Return the currently active graph."""
        return self._active_graph

    def reset_graph(self) -> Graph:
        """
        Restore the active graph to the original loaded graph,
        discarding all search/filter operations.
        """
        if self._original_graph is None:
            raise ValueError("No graph loaded")
        self._active_graph = copy.deepcopy(self._original_graph)
        return self._active_graph

    def clear_graph(self) -> None:
        """Remove all nodes and edges from the active graph."""
        if self._active_graph is None:
            raise ValueError("No graph loaded")
        for edge in list(self._active_graph.edges):
            self._active_graph.remove_edge(edge)
        for node in list(self._active_graph.nodes):
            self._active_graph.remove_node(node)

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    def visualize(self, visualizer_id: str, **kwargs) -> str:
        """
        Visualize the active graph using the specified visualizer plugin.

        Args:
            visualizer_id: identifier of the visualizer plugin (e.g. 'simple', 'block')
            **kwargs: plugin-specific args (e.g. width=800, height=600, layout='force')

        Returns:
            SVG string
        """
        self._require_graph()
        plugin = self._viz_factory.create_plugin(visualizer_id)
        return plugin.visualize(self._active_graph, **kwargs)

    # ------------------------------------------------------------------
    # Search & Filter
    # ------------------------------------------------------------------

    def search(self, text: str) -> Graph:
        """
        Search the active graph and update it with the resulting subgraph.

        Args:
            text: search query

        Returns:
            The new active graph (subgraph)
        """
        self._require_graph()
        self._active_graph = self._active_graph.search(text)
        return self._active_graph

    def filter(self, expr: str) -> Graph:
        """
        Filter the active graph and update it with the resulting subgraph.

        Args:
            expr: filter expression e.g. 'age > 30'

        Returns:
            The new active graph (subgraph)
        """
        self._require_graph()
        self._active_graph = self._active_graph.filter(expr)
        return self._active_graph

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def add_node(self, node_id: str, **attributes) -> Node:
        """
        Add a new node to the active graph.

        Args:
            node_id: unique node identifier
            **attributes: key=value pairs, values are auto-typed

        Returns:
            The created Node
        """
        self._require_graph()
        node = Node(node_id)
        for key, value in attributes.items():
            attr = self._parse_attribute(value)
            node.add_attribute(key, attr)
        self._active_graph.add_node(node)
        return node

    def remove_node(self, node_id: str) -> None:
        """
        Remove a node from the active graph.
        Raises ValueError if node has connected edges.

        Args:
            node_id: id of node to remove
        """
        self._require_graph()
        node = self._get_node_or_raise(node_id)
        self._active_graph.remove_node(node)

    def edit_node(self, node_id: str, **attributes) -> Node:
        """
        Edit attributes of an existing node.
        Existing attributes are updated; new ones are added.

        Args:
            node_id: id of node to edit
            **attributes: key=value pairs to update

        Returns:
            The updated Node
        """
        self._require_graph()
        node = self._get_node_or_raise(node_id)
        for key, value in attributes.items():
            attr = self._parse_attribute(value)
            node.add_attribute(key, attr)
        return node

    # ------------------------------------------------------------------
    # Edge operations
    # ------------------------------------------------------------------

    def add_edge(self, source_id: str, target_id: str, label: str = "") -> Edge:
        """
        Add a new edge between two existing nodes.

        Args:
            source_id: id of source node
            target_id: id of target node
            label:     optional edge label

        Returns:
            The created Edge
        """
        self._require_graph()
        source = self._get_node_or_raise(source_id)
        target = self._get_node_or_raise(target_id)
        return self._active_graph.add_edge(source, target, label)

    def remove_edge(self, edge_id: str) -> None:
        """
        Remove an edge from the active graph.

        Args:
            edge_id: id of edge to remove
        """
        self._require_graph()
        edge = self._active_graph.get_edge(edge_id)
        if edge is None:
            raise ValueError(f"Edge '{edge_id}' not found")
        self._active_graph.remove_edge(edge)

    def edit_edge(self, edge_id: str, **attributes) -> Edge:
        """
        Edit attributes of an existing edge.

        Args:
            edge_id: id of edge to edit
            **attributes: key=value pairs to update

        Returns:
            The updated Edge
        """
        self._require_graph()
        edge = self._active_graph.get_edge(edge_id)
        if edge is None:
            raise ValueError(f"Edge '{edge_id}' not found")
        for key, value in attributes.items():
            attr = self._parse_attribute(value)
            edge.add_attribute(key, attr)
        return edge

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_graph(self) -> None:
        if self._active_graph is None:
            raise ValueError("No graph loaded. Use load_graph() first.")

    def _get_node_or_raise(self, node_id: str) -> Node:
        node = self._active_graph.get_node(node_id)
        if node is None:
            raise ValueError(f"Node '{node_id}' not found")
        return node

    @staticmethod
    def _parse_attribute(value: str) -> AttributeValue:
        """
        Auto-detect type from string value and return AttributeValue.
        Order: int -> float -> str
        """
        if isinstance(value, AttributeValue):
            return value
        s = str(value)
        try:
            return AttributeValue(AttributeType.INT, int(s))
        except ValueError:
            pass
        try:
            return AttributeValue(AttributeType.FLOAT, float(s))
        except ValueError:
            pass
        return AttributeValue(AttributeType.STR, s)