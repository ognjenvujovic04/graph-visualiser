from typing import Optional
from datetime import datetime

from graph.api.model.graph import Graph
from graph.api.model.node import Node
from graph.api.model.edge import Edge
from graph.api.model.attributes import AttributeValue, AttributeType
from graph.use_cases.plugin_recognition import PluginRegistry
from graph.factory.data_source_factory import DataSourceFactory
from graph.factory.visualizer_factory import VisualizerFactory
from graph.workspaces.workspace_manager import WorkspaceManager


class PlatformFacade:
    """
    Single entry point for all platform operations.
    Django, Flask and CLI all go through this class exclusively.
    Implemented as a Singleton.
    """

    _instance: Optional['PlatformFacade'] = None

    def __new__(cls) -> 'PlatformFacade':
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._initialized = False
            cls._instance = inst
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._registry = PluginRegistry()
        self._registry.load_all()

        self._ds_factory = DataSourceFactory(self._registry)
        self._viz_factory = VisualizerFactory(self._registry)
        self._workspace_manager = WorkspaceManager()

    # ------------------------------------------------------------------
    # Singleton access
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> 'PlatformFacade':
        """Convenience class method — equivalent to PlatformFacade()."""
        return cls()

    # ------------------------------------------------------------------
    # Plugin info
    # ------------------------------------------------------------------

    def get_datasources(self) -> list:
        """Return list of available datasource plugins."""
        return self._registry.datasources

    def get_visualizers(self) -> list:
        """Return list of available visualizer plugins."""
        return self._registry.visualizers

    def get_datasource_ids(self) -> list:
        """Return list of datasource plugin identifiers."""
        return [p.identifier() for p in self._registry.datasources]

    def get_visualizer_ids(self) -> list:
        """Return list of visualizer plugin identifiers."""
        return [p.identifier() for p in self._registry.visualizers]

    # ------------------------------------------------------------------
    # Graph loading
    # ------------------------------------------------------------------

    def load_graph(self, plugin_id: str, workspace_name: str = "default", **kwargs) -> Graph:
        """
        Load a graph using the specified datasource plugin.
        Creates a new workspace or replaces existing one with same name.

        Raises ValueError if plugin_id is not found.
        """
        if plugin_id not in self.get_datasource_ids():
            raise ValueError(
                f"Unknown datasource plugin: '{plugin_id}'. "
                f"Available: {self.get_datasource_ids()}"
            )

        plugin = self._ds_factory.create_plugin(plugin_id)

        if workspace_name in self._workspace_manager.workspaces:
            self._workspace_manager.delete_workspace(workspace_name)

        ws = self._workspace_manager.create_workspace_from_plugin(
            plugin, workspace_name, **kwargs
        )
        self._workspace_manager.switch_workspace(workspace_name)
        return ws.get_active_graph()

    def get_active_graph(self) -> Optional[Graph]:
        """Return the currently active graph."""
        return self._workspace_manager.get_active_graph()

    def reset_graph(self) -> Graph:
        """Restore active graph to original, discarding search/filter history."""
        ws = self._require_workspace()
        ws.reset_active_graph()
        return ws.get_active_graph()

    def clear_graph(self) -> None:
        """Remove all nodes and edges from the active graph."""
        graph = self._require_graph()
        # First remove all edges so nodes become disconnected
        for edge in list(graph.edges):
            graph.remove_edge(edge)
        # Then remove all nodes (safe — no connected edges remain)
        for node in list(graph.nodes):
            graph.remove_node(node)

    # ------------------------------------------------------------------
    # Workspace operations
    # ------------------------------------------------------------------

    def get_workspace_manager(self) -> WorkspaceManager:
        return self._workspace_manager

    def create_workspace(self, name: str, plugin_id: str, **kwargs) -> None:
        """Create a new workspace and switch to it."""
        if plugin_id not in self.get_datasource_ids():
            raise ValueError(
                f"Unknown datasource plugin: '{plugin_id}'. "
                f"Available: {self.get_datasource_ids()}"
            )
        plugin = self._ds_factory.create_plugin(plugin_id)
        self._workspace_manager.create_workspace_from_plugin(plugin, name, **kwargs)
        self._workspace_manager.switch_workspace(name)

    def switch_workspace(self, name: str) -> None:
        """Switch to an existing workspace."""
        self._workspace_manager.switch_workspace(name)

    def list_workspaces(self) -> dict:
        """Return all workspaces."""
        return self._workspace_manager.list_workspaces()

    def delete_workspace(self, name: str) -> None:
        """Delete a workspace by name."""
        self._workspace_manager.delete_workspace(name)

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    def visualize(self, visualizer_id: str, **kwargs) -> str:
        """
        Visualize the active graph using the specified visualizer plugin.
        Returns SVG/HTML string.

        Raises ValueError if visualizer_id is not found.
        """
        if visualizer_id not in self.get_visualizer_ids():
            raise ValueError(
                f"Unknown visualizer plugin: '{visualizer_id}'. "
                f"Available: {self.get_visualizer_ids()}"
            )
        graph = self._require_graph()
        plugin = self._viz_factory.create_plugin(visualizer_id)
        return plugin.visualize(graph, **kwargs)

    # ------------------------------------------------------------------
    # Search & Filter
    # ------------------------------------------------------------------

    def search(self, text: str) -> Graph:
        """Search the active graph. Updates workspace active graph."""
        ws = self._require_workspace()
        ws.apply_search(text)
        return ws.get_active_graph()

    def filter(self, expr: str) -> Graph:
        """Filter the active graph. Updates workspace active graph."""
        ws = self._require_workspace()
        ws.apply_filter(expr)
        return ws.get_active_graph()

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def add_node(self, node_id: str, **attributes) -> Node:
        """Add a new node to the active graph."""
        graph = self._require_graph()
        node = Node(node_id)
        for key, value in attributes.items():
            node.add_attribute(key, self._parse_attribute(value))
        graph.add_node(node)
        return node

    def remove_node(self, node_id: str) -> None:
        """
        Remove a node from the active graph.
        Raises ValueError if node has connected edges.
        """
        graph = self._require_graph()
        node = self._get_node_or_raise(graph, node_id)
        graph.remove_node(node)

    def edit_node(self, node_id: str, **attributes) -> Node:
        """Edit attributes of an existing node."""
        graph = self._require_graph()
        node = self._get_node_or_raise(graph, node_id)
        for key, value in attributes.items():
            node.add_attribute(key, self._parse_attribute(value))
        return node

    # ------------------------------------------------------------------
    # Edge operations
    # ------------------------------------------------------------------

    def add_edge(self, source_id: str, target_id: str, label: str = "") -> Edge:
        """Add a new edge between two existing nodes."""
        graph = self._require_graph()
        source = self._get_node_or_raise(graph, source_id)
        target = self._get_node_or_raise(graph, target_id)
        return graph.add_edge(source, target, label)

    def remove_edge(self, edge_id: str) -> None:
        """Remove an edge from the active graph."""
        graph = self._require_graph()
        edge = graph.get_edge(edge_id)
        if edge is None:
            raise ValueError(f"Edge '{edge_id}' not found")
        graph.remove_edge(edge)

    def edit_edge(self, edge_id: str, **attributes) -> Edge:
        """Edit attributes of an existing edge."""
        graph = self._require_graph()
        edge = graph.get_edge(edge_id)
        if edge is None:
            raise ValueError(f"Edge '{edge_id}' not found")
        for key, value in attributes.items():
            edge.add_attribute(key, self._parse_attribute(value))
        return edge

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_workspace(self):
        ws = self._workspace_manager.get_active_workspace()
        if ws is None:
            raise ValueError("No workspace loaded. Use load_graph() first.")
        return ws

    def _require_graph(self) -> Graph:
        graph = self._workspace_manager.get_active_graph()
        if graph is None:
            raise ValueError("No graph loaded. Use load_graph() first.")
        return graph

    def _get_node_or_raise(self, graph: Graph, node_id: str) -> Node:
        node = graph.get_node(node_id)
        if node is None:
            raise ValueError(f"Node '{node_id}' not found")
        return node

    # ------------------------------------------------------------------
    # Attribute parsing — supports int, float, date, str
    # ------------------------------------------------------------------

    # Date formats to try when auto-detecting
    _DATE_FORMATS = [
        "%Y-%m-%d",       # 2024-01-15
        "%d.%m.%Y",       # 15.01.2024
        "%d/%m/%Y",       # 15/01/2024
        "%m/%d/%Y",       # 01/15/2024
        "%Y-%m-%dT%H:%M:%S",  # 2024-01-15T10:30:00
    ]

    @staticmethod
    def _parse_attribute(value) -> AttributeValue:
        """
        Auto-detect type from value and return AttributeValue.
        Detection order: int -> float -> date -> str
        Covers all four required types from the specification.
        """
        if isinstance(value, AttributeValue):
            return value

        # Already typed Python values
        if isinstance(value, int) and not isinstance(value, bool):
            return AttributeValue(AttributeType.INT, value)
        if isinstance(value, float):
            return AttributeValue(AttributeType.FLOAT, value)
        if isinstance(value, datetime):
            return AttributeValue(AttributeType.DATE, value)

        s = str(value).strip()

        # Try int
        try:
            return AttributeValue(AttributeType.INT, int(s))
        except ValueError:
            pass

        # Try float
        try:
            return AttributeValue(AttributeType.FLOAT, float(s))
        except ValueError:
            pass

        # Try date (multiple formats)
        for fmt in PlatformFacade._DATE_FORMATS:
            try:
                dt = datetime.strptime(s, fmt)
                return AttributeValue(AttributeType.DATE, dt)
            except ValueError:
                continue

        # Fallback: string
        return AttributeValue(AttributeType.STR, s)