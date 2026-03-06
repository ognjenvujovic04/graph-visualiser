import json
from datetime import date, datetime
from pathlib import Path

from graph.api.services.plugin import VisualizerPlugin
from graph.api.model.graph import Graph
from graph.api.model.attributes import AttributeValue


class BlockVisualizer(VisualizerPlugin):
    """
    Block visualizer plugin — renders each node as a rectangle
    showing the node ID in a header and all attributes as key/value rows.
    The returned HTML includes CSS, D3 script, and serialized graph data.
    """

    _TEMPLATE_DIR = Path(__file__).with_name("templates")

    def name(self) -> str:
        return "Block Visualizer"

    def identifier(self) -> str:
        return "block"

    def visualize(self, graph: Graph, **kwargs) -> str:
        """
        Visualize the graph as an HTML string with block-style nodes.

        kwargs:
            - width: canvas width in pixels (default: 900)
            - height: canvas height in pixels (default: 700)
            - theme: color theme "dark" or "light" (default: "dark")

        Returns:
            HTML string representation of the graph
        """
        if not isinstance(graph, Graph):
            raise TypeError("graph must be a Graph instance")

        width = kwargs.get("width", 900)
        height = kwargs.get("height", 700)
        theme = kwargs.get("theme", "dark")

        if not isinstance(width, int) or width <= 0:
            raise ValueError("width must be a positive integer")
        if not isinstance(height, int) or height <= 0:
            raise ValueError("height must be a positive integer")
        if theme not in ("dark", "light"):
            raise ValueError("theme must be 'dark' or 'light'")

        nodes_payload = [
            {
                "id": str(node.id),
                "data": self._sanitize_attributes(node.attributes),
            }
            for node in graph.nodes
        ]

        edges_payload = [
            {
                "source": str(edge.source.id),
                "target": str(edge.target.id),
                "directed": graph.directed,
                "label": edge.label,
                "data": self._sanitize_attributes(edge.attributes),
            }
            for edge in graph.edges
        ]

        nodes_json = self._json_for_script(nodes_payload)
        edges_json = self._json_for_script(edges_payload)

        template = self._load_template(theme)
        return (
            template
            .replace("__WIDTH__", str(width))
            .replace("__HEIGHT__", str(height))
            .replace("__NODES_JSON__", nodes_json)
            .replace("__EDGES_JSON__", edges_json)
        ).strip()

    def _load_template(self, theme: str = "dark") -> str:
        template_path = self._TEMPLATE_DIR / f"block_visualizer_{theme}.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text(encoding="utf-8")

    def _safe_value(self, value):
        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y. %H:%M")
        if isinstance(value, date):
            return value.strftime("%d.%m.%Y.")
        return str(value)

    def _sanitize_attributes(self, attributes) -> dict:
        if not isinstance(attributes, dict):
            return {}

        sanitized = {}
        for key, attr_value in attributes.items():
            if key is None or attr_value is None:
                continue

            raw_value = attr_value
            if isinstance(attr_value, AttributeValue):
                raw_value = attr_value.value

            sanitized[str(key)] = self._safe_value(raw_value)

        return sanitized

    def _json_for_script(self, value) -> str:
        return json.dumps(value).replace("</", "<\\/")