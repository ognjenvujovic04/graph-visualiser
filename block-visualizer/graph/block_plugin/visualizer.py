from graph.api.services.plugin import VisualizerPlugin
from graph.api.model.graph import Graph
from .renderer import BlockRenderer


class BlockVisualizer(VisualizerPlugin):
    """
    Block visualizer plugin — renders each node as a rectangle
    showing the node ID in a header and all attributes as key/value rows.
    """

    def __init__(self):
        self.__renderer = BlockRenderer()

    def name(self) -> str:
        return "Block Visualizer"

    def identifier(self) -> str:
        return "block"

    def visualize(self, graph: Graph, **kwargs) -> str:
        """
        Visualize the graph as an SVG string with block-style nodes.

        kwargs:
            width  (int): canvas width  (default 900)
            height (int): canvas height (default 700)
            layout (str): 'force' | 'circle' | 'grid'  (default 'force')

        Returns:
            SVG string
        """
        if not isinstance(graph, Graph):
            raise TypeError("graph must be a Graph instance")

        width = kwargs.get("width", 900)
        height = kwargs.get("height", 700)
        layout = kwargs.get("layout", "force")

        if not isinstance(width, int) or width <= 0:
            raise ValueError("width must be a positive integer")
        if not isinstance(height, int) or height <= 0:
            raise ValueError("height must be a positive integer")
        if layout not in ("force", "circle", "grid"):
            raise ValueError("layout must be 'force', 'circle', or 'grid'")

        return self.__renderer.render(graph, width=width, height=height, layout=layout)