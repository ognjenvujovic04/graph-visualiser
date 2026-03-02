import math
from typing import Dict, Tuple
from graph.api.model.graph import Graph
from graph.api.model.node import Node
import random


class SvgRenderer:
    """Renders graph as SVG using force-directed or basic layouts."""

    def render(
        self,
        graph: Graph,
        width: int,
        height: int,
        node_radius: int,
        layout: str = "force"
    ) -> str:
        """
        Render graph as SVG.
        
        Args:
            graph: Graph to render
            width: SVG canvas width
            height: SVG canvas height
            node_radius: Radius of each node circle
            layout: Layout strategy ('force', 'circle', 'grid')
        
        Returns:
            SVG string
        """
        # Calculate node positions based on layout
        if layout == "circle":
            positions = self._layout_circle(graph, width, height, node_radius)
        elif layout == "grid":
            positions = self._layout_grid(graph, width, height, node_radius)
        else:  # Default to force or any unknown layout
            positions = self._layout_force(graph, width, height, node_radius)

        # Build SVG
        svg = self._build_svg(graph, positions, width, height, node_radius)
        return svg

    def _layout_circle(
        self,
        graph: Graph,
        width: int,
        height: int,
        node_radius: int
    ) -> Dict[str, Tuple[float, float]]:
        """Place nodes in a circle."""
        positions: Dict[str, Tuple[float, float]] = {}
        nodes = graph.nodes
        num_nodes = len(nodes)

        if num_nodes == 0:
            return positions

        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) // 2 - node_radius - 20

        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / num_nodes
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[node.id] = (x, y)

        return positions

    def _layout_grid(
        self,
        graph: Graph,
        width: int,
        height: int,
        node_radius: int
    ) -> Dict[str, Tuple[float, float]]:
        """Place nodes in a grid."""
        positions: Dict[str, Tuple[float, float]] = {}
        nodes = graph.nodes
        num_nodes = len(nodes)

        if num_nodes == 0:
            return positions

        # Calculate grid dimensions
        cols = int(math.ceil(math.sqrt(num_nodes)))
        rows = int(math.ceil(num_nodes / cols))

        # Calculate spacing
        spacing_x = width / (cols + 1)
        spacing_y = height / (rows + 1)

        for i, node in enumerate(nodes):
            row = i // cols
            col = i % cols
            x = spacing_x * (col + 1)
            y = spacing_y * (row + 1)
            positions[node.id] = (x, y)

        return positions

    def _layout_force(
        self,
        graph: Graph,
        width: int,
        height: int,
        node_radius: int,
        iterations: int = 100
    ) -> Dict[str, Tuple[float, float]]:
        """
        Simple force-directed layout algorithm.
        Uses repulsive forces between nodes and attractive forces along edges.
        """
        positions = {}
        nodes = graph.nodes

        if len(nodes) == 0:
            return positions

        # Initialize positions randomly
        for node in nodes:
            positions[node.id] = (
                random.uniform(node_radius, width - node_radius),
                random.uniform(node_radius, height - node_radius),
            )

        area = width * height
        k = math.sqrt(area / len(nodes))
        temperature = width / 10

        # Iteration loop
        for _ in range(iterations):
            # Reset forces
            forces = {node.id: (0.0, 0.0) for node in nodes}

            # --- Repulsion ---
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i + 1:]:
                    x1, y1 = positions[node1.id]
                    x2, y2 = positions[node2.id]

                    dx = x2 - x1
                    dy = y2 - y1
                    dist = math.sqrt(dx * dx + dy * dy) + 0.01

                    force = (k * k) / dist

                    fx = force * dx / dist
                    fy = force * dy / dist

                    forces[node1.id] = (
                        forces[node1.id][0] - fx,
                        forces[node1.id][1] - fy,
                    )
                    forces[node2.id] = (
                        forces[node2.id][0] + fx,
                        forces[node2.id][1] + fy,
                    )

            # --- Attraction ---
            for edge in graph.edges:
                x1, y1 = positions[edge.source.id]
                x2, y2 = positions[edge.target.id]

                dx = x2 - x1
                dy = y2 - y1
                dist = math.sqrt(dx * dx + dy * dy) + 0.01

                force = (dist * dist) / k

                fx = force * dx / dist
                fy = force * dy / dist

                forces[edge.source.id] = (
                    forces[edge.source.id][0] + fx,
                    forces[edge.source.id][1] + fy,
                )
                forces[edge.target.id] = (
                    forces[edge.target.id][0] - fx,
                    forces[edge.target.id][1] - fy,
                )

            # --- Move nodes ---
            for node in nodes:
                fx, fy = forces[node.id]
                x, y = positions[node.id]

                # limit movement by temperature
                dx = max(-temperature, min(temperature, fx))
                dy = max(-temperature, min(temperature, fy))

                x += dx
                y += dy

                # keep inside bounds
                x = min(width - node_radius, max(node_radius, x))
                y = min(height - node_radius, max(node_radius, y))

                positions[node.id] = (x, y)

            # cool down
            temperature *= 0.95

        return positions

    def _build_svg(
        self,
        graph: Graph,
        positions: Dict[str, Tuple[float, float]],
        width: int,
        height: int,
        node_radius: int
    ) -> str:
        """Build SVG string from graph and node positions."""
        svg_parts = [
            f'<svg width="{width}" height="{height}" '
            f'xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #ccc;">',
            f'<defs><style>.node-text {{ font-size: 12px; text-anchor: middle; '
            f'dominant-baseline: middle; }}</style></defs>',
        ]

        # Draw edges first (so they appear behind nodes)
        for edge in graph.edges:
            x1, y1 = positions[edge.source.id]
            x2, y2 = positions[edge.target.id]

            # Draw line
            svg_parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" '
                f'x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#999" stroke-width="1" />'
            )

            # Draw arrowhead if directed
            if graph.directed:
                svg_parts.append(
                    self._get_arrowhead_svg(x1, y1, x2, y2, node_radius)
                )

        # Draw nodes
        for node in graph.nodes:
            x, y = positions[node.id]
            svg_parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{node_radius}" '
                f'fill="#87CEEB" stroke="#333" stroke-width="2" />'
            )
            svg_parts.append(
                f'<text x="{x:.1f}" y="{y:.1f}" class="node-text" '
                f'style="pointer-events: none;">{node.id}</text>'
            )

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    @staticmethod
    def _get_arrowhead_svg(x1: float, y1: float, x2: float, y2: float, node_radius: int) -> str:
        """Generate SVG for arrowhead at end of edge."""
        # Calculate direction
        dx = x2 - x1
        dy = y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.01:
            return ""

        # Arrow parameters
        arrow_size = 10
        arrow_angle = math.pi / 6  # 30 degrees

        # Position arrow at node edge
        norm_x = dx / dist
        norm_y = dy / dist
        
        # Arrow tip position (at node boundary)
        arrow_x = x2 - norm_x * node_radius
        arrow_y = y2 - norm_y * node_radius

        # Arrow base positions
        angle = math.atan2(dy, dx)
        p1_x = arrow_x - arrow_size * math.cos(angle - arrow_angle)
        p1_y = arrow_y - arrow_size * math.sin(angle - arrow_angle)
        p2_x = arrow_x - arrow_size * math.cos(angle + arrow_angle)
        p2_y = arrow_y - arrow_size * math.sin(angle + arrow_angle)

        return (
            f'<polygon points="{arrow_x:.1f},{arrow_y:.1f} '
            f'{p1_x:.1f},{p1_y:.1f} {p2_x:.1f},{p2_y:.1f}" '
            f'fill="#333" />'
        )
