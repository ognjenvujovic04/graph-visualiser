from graph.api.services.plugin import VisualizerPlugin
from graph.api.model.graph import Graph
from .renderer import SvgRenderer


class SimpleVisualizer(VisualizerPlugin):
    """
    Simple visualizer plugin that renders graphs as SVG.
    Each node is represented as a circle with its ID labeled.
    Edges are drawn as lines connecting the nodes.
    """

    def __init__(self):
        self.__renderer = SvgRenderer()

    def name(self) -> str:
        return "Simple Visualizer"

    def identifier(self) -> str:
        return "simple"

    def visualize(self, graph: Graph, **kwargs) -> str:
        """
        Visualize the graph as an SVG string.
        
        kwargs:
            - width: SVG canvas width (default: 800)
            - height: SVG canvas height (default: 600)
            - node_radius: radius of each node circle (default: 30)
            - layout: layout strategy (default: 'force') - can be 'force', 'circle', 'grid'
        
        Returns:
            SVG string representation of the graph
        """
        if not isinstance(graph, Graph):
            raise TypeError("graph must be Graph instance")

        # Extract parameters from kwargs
        width = kwargs.get("width", 800)
        height = kwargs.get("height", 600)
        node_radius = kwargs.get("node_radius", 30)
        layout = kwargs.get("layout", "force")

        # Validate parameters
        if not isinstance(width, int) or width <= 0:
            raise ValueError("width must be positive integer")
        if not isinstance(height, int) or height <= 0:
            raise ValueError("height must be positive integer")
        if not isinstance(node_radius, int) or node_radius <= 0:
            raise ValueError("node_radius must be positive integer")

        # Render and return SVG
        return self.__renderer.render(
            graph,
            width=width,
            height=height,
            node_radius=node_radius,
            layout=layout
        )
