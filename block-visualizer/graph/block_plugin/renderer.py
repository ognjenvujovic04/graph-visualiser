import math
import random
from typing import Dict, Tuple
from graph.api.model.graph import Graph
from graph.api.model.node import Node


# Block dimensions
BLOCK_W = 160
BLOCK_H_BASE = 40   # header height
BLOCK_ROW_H = 18    # height per attribute row
BLOCK_PAD = 8       # internal padding


def _block_height(node: Node) -> int:
    return BLOCK_H_BASE + max(1, len(node.attributes)) * BLOCK_ROW_H + BLOCK_PAD


class BlockRenderer:
    """Renders graph as SVG where each node is a block/rectangle with attributes."""

    def render(self, graph: Graph, width: int, height: int, layout: str = "force") -> str:
        positions = self._layout(graph, width, height, layout)
        return self._build_svg(graph, positions, width, height)

    # ------------------------------------------------------------------
    # Layouts
    # ------------------------------------------------------------------

    def _layout(self, graph: Graph, width: int, height: int, layout: str) -> Dict[str, Tuple[float, float]]:
        if layout == "circle":
            return self._layout_circle(graph, width, height)
        elif layout == "grid":
            return self._layout_grid(graph, width, height)
        else:
            return self._layout_force(graph, width, height)

    def _layout_circle(self, graph: Graph, width: int, height: int) -> Dict[str, Tuple[float, float]]:
        positions: Dict[str, Tuple[float, float]] = {}
        nodes = graph.nodes
        n = len(nodes)
        if n == 0:
            return positions
        cx, cy = width / 2, height / 2
        r = min(width, height) / 2 - BLOCK_W // 2 - 20
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / n
            positions[node.id] = (cx + r * math.cos(angle), cy + r * math.sin(angle))
        return positions

    def _layout_grid(self, graph: Graph, width: int, height: int) -> Dict[str, Tuple[float, float]]:
        positions: Dict[str, Tuple[float, float]] = {}
        nodes = graph.nodes
        n = len(nodes)
        if n == 0:
            return positions
        cols = max(1, int(math.ceil(math.sqrt(n))))
        rows = int(math.ceil(n / cols))
        sx = width / (cols + 1)
        sy = height / (rows + 1)
        for i, node in enumerate(nodes):
            positions[node.id] = (sx * (i % cols + 1), sy * (i // cols + 1))
        return positions

    def _layout_force(self, graph: Graph, width: int, height: int, iterations: int = 120) -> Dict[str, Tuple[float, float]]:
        positions: Dict[str, Tuple[float, float]] = {}
        nodes = graph.nodes
        if not nodes:
            return positions

        for node in nodes:
            positions[node.id] = (
                random.uniform(BLOCK_W, width - BLOCK_W),
                random.uniform(BLOCK_H_BASE, height - BLOCK_H_BASE),
            )

        area = width * height
        k = math.sqrt(area / len(nodes))
        temp = width / 10

        for _ in range(iterations):
            forces = {node.id: [0.0, 0.0] for node in nodes}

            # repulsion
            for i, n1 in enumerate(nodes):
                for n2 in nodes[i + 1:]:
                    dx = positions[n2.id][0] - positions[n1.id][0]
                    dy = positions[n2.id][1] - positions[n1.id][1]
                    dist = math.sqrt(dx * dx + dy * dy) + 0.01
                    f = (k * k) / dist
                    fx, fy = f * dx / dist, f * dy / dist
                    forces[n1.id][0] -= fx
                    forces[n1.id][1] -= fy
                    forces[n2.id][0] += fx
                    forces[n2.id][1] += fy

            # attraction
            for edge in graph.edges:
                dx = positions[edge.target.id][0] - positions[edge.source.id][0]
                dy = positions[edge.target.id][1] - positions[edge.source.id][1]
                dist = math.sqrt(dx * dx + dy * dy) + 0.01
                f = (dist * dist) / k
                fx, fy = f * dx / dist, f * dy / dist
                forces[edge.source.id][0] += fx
                forces[edge.source.id][1] += fy
                forces[edge.target.id][0] -= fx
                forces[edge.target.id][1] -= fy

            # move
            for node in nodes:
                fx = max(-temp, min(temp, forces[node.id][0]))
                fy = max(-temp, min(temp, forces[node.id][1]))
                x = max(BLOCK_W // 2, min(width - BLOCK_W // 2, positions[node.id][0] + fx))
                y = max(BLOCK_H_BASE, min(height - BLOCK_H_BASE, positions[node.id][1] + fy))
                positions[node.id] = (x, y)

            temp *= 0.95

        return positions

    # ------------------------------------------------------------------
    # SVG builder
    # ------------------------------------------------------------------

    def _build_svg(self, graph: Graph, positions: Dict[str, Tuple[float, float]], width: int, height: int) -> str:
        parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" '
            f'style="border:1px solid #ccc; background:#fafafa;">',
            '<defs>',
            '  <style>',
            '    .blk-header { font: bold 12px monospace; fill: #fff; }',
            '    .blk-attr-key { font: 11px monospace; fill: #555; }',
            '    .blk-attr-val { font: 11px monospace; fill: #111; }',
            '    .blk-divider { stroke: #c0c8d0; stroke-width: 1; }',
            '  </style>',
            '</defs>',
        ]

        # edges first
        for edge in graph.edges:
            sx, sy = positions[edge.source.id]
            tx, ty = positions[edge.target.id]
            parts.append(
                f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" '
                f'stroke="#aaa" stroke-width="1.5"/>'
            )
            if graph.directed:
                parts.append(self._arrowhead(sx, sy, tx, ty))
            if edge.label:
                mx, my = (sx + tx) / 2, (sy + ty) / 2
                parts.append(
                    f'<text x="{mx:.1f}" y="{my - 4:.1f}" '
                    f'font-size="10" fill="#888" text-anchor="middle">{edge.label}</text>'
                )

        # nodes
        for node in graph.nodes:
            cx, cy = positions[node.id]
            bh = _block_height(node)
            x = cx - BLOCK_W / 2
            y = cy - bh / 2

            # outer rect
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{BLOCK_W}" height="{bh}" '
                f'rx="6" ry="6" fill="#ffffff" stroke="#5b8fa8" stroke-width="1.5"/>'
            )
            # header bg
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{BLOCK_W}" height="{BLOCK_H_BASE}" '
                f'rx="6" ry="6" fill="#5b8fa8"/>'
            )
            # cover bottom-round of header
            parts.append(
                f'<rect x="{x:.1f}" y="{y + BLOCK_H_BASE / 2:.1f}" width="{BLOCK_W}" height="{BLOCK_H_BASE / 2:.1f}" '
                f'fill="#5b8fa8"/>'
            )
            # node id in header
            parts.append(
                f'<text x="{cx:.1f}" y="{y + BLOCK_H_BASE / 2:.1f}" '
                f'class="blk-header" text-anchor="middle" dominant-baseline="middle">'
                f'{node.id}</text>'
            )
            # divider
            dy_div = y + BLOCK_H_BASE
            parts.append(
                f'<line x1="{x:.1f}" y1="{dy_div:.1f}" x2="{x + BLOCK_W:.1f}" y2="{dy_div:.1f}" '
                f'class="blk-divider"/>'
            )

            # attributes
            attrs = node.attributes
            if attrs:
                for i, (k, v) in enumerate(attrs.items()):
                    row_y = dy_div + BLOCK_ROW_H * i + BLOCK_ROW_H / 2
                    # key
                    parts.append(
                        f'<text x="{x + 6:.1f}" y="{row_y:.1f}" '
                        f'class="blk-attr-key" dominant-baseline="middle">{k}:</text>'
                    )
                    # value (truncate if too long)
                    val_str = str(v.value)
                    if len(val_str) > 12:
                        val_str = val_str[:11] + "…"
                    parts.append(
                        f'<text x="{x + BLOCK_W - 6:.1f}" y="{row_y:.1f}" '
                        f'class="blk-attr-val" text-anchor="end" dominant-baseline="middle">{val_str}</text>'
                    )
            else:
                row_y = dy_div + BLOCK_ROW_H / 2
                parts.append(
                    f'<text x="{cx:.1f}" y="{row_y:.1f}" '
                    f'font-size="10" fill="#bbb" text-anchor="middle" dominant-baseline="middle">'
                    f'(no attributes)</text>'
                )

        parts.append("</svg>")
        return "\n".join(parts)

    @staticmethod
    def _arrowhead(x1: float, y1: float, x2: float, y2: float) -> str:
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx * dx + dy * dy) + 0.01
        nx, ny = dx / dist, dy / dist
        tip_x = x2 - nx * (BLOCK_W / 2 + 4)
        tip_y = y2 - ny * (BLOCK_H_BASE / 2 + 4)
        angle = math.atan2(dy, dx)
        size, spread = 10, math.pi / 6
        p1x = tip_x - size * math.cos(angle - spread)
        p1y = tip_y - size * math.sin(angle - spread)
        p2x = tip_x - size * math.cos(angle + spread)
        p2y = tip_y - size * math.sin(angle + spread)
        return (
            f'<polygon points="{tip_x:.1f},{tip_y:.1f} {p1x:.1f},{p1y:.1f} {p2x:.1f},{p2y:.1f}" '
            f'fill="#555"/>'
        )