import random
from pathlib import Path

from graph.api.model.graph import Graph
from graph.api.model.node import Node
from graph.api.model.attributes import AttributeValue, AttributeType
from graph.block_plugin.visualizer import BlockVisualizer

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


class BlockVisualizerTestSuite:

    def __init__(self):
        self.visualizer = BlockVisualizer()
        self.passed = 0
        self.failed = 0

    def save_svg(self, filename: str, svg: str) -> str:
        filepath = OUTPUT_DIR / filename
        with open(filepath, "w") as f:
            f.write(svg)
        return str(filepath)

    # ------------------------------------------------------------------

    def test_directed_graph(self):
        """Test 1: Basic directed graph."""
        try:
            g = Graph(directed=True, cyclic=True)
            nodes = [Node(name) for name in ["Alice", "Bob", "Charlie"]]
            for n in nodes:
                g.add_node(n)
            g.add_edge(nodes[0], nodes[1], label="knows")
            g.add_edge(nodes[1], nodes[2], label="works_with")
            g.add_edge(nodes[2], nodes[0], label="respects")

            svg = self.visualizer.visualize(g, width=800, height=600)
            self.save_svg("blk_01_directed.svg", svg)

            assert "<rect" in svg, "Expected rect elements"
            assert "Alice" in svg
            print("✓ Test 1 PASSED: Directed graph")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 1 FAILED: {e}")
            self.failed += 1

    def test_undirected_graph(self):
        """Test 2: Undirected graph, circle layout."""
        try:
            g = Graph(directed=False, cyclic=True)
            nodes = [Node(f"N{i}") for i in range(5)]
            for n in nodes:
                g.add_node(n)
            for i in range(5):
                g.add_edge(nodes[i], nodes[(i + 1) % 5])

            svg = self.visualizer.visualize(g, width=800, height=600, layout="circle")
            self.save_svg("blk_02_undirected_circle.svg", svg)

            assert "<rect" in svg
            print("✓ Test 2 PASSED: Undirected graph, circle layout")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 2 FAILED: {e}")
            self.failed += 1

    def test_nodes_with_attributes(self):
        """Test 3: Nodes with multiple typed attributes."""
        try:
            g = Graph(directed=True, cyclic=False)

            alice = Node("Alice")
            alice.add_attribute("age",  AttributeValue(AttributeType.INT, 30))
            alice.add_attribute("role", AttributeValue(AttributeType.STR, "Engineer"))
            alice.add_attribute("score", AttributeValue(AttributeType.FLOAT, 9.5))

            bob = Node("Bob")
            bob.add_attribute("age",  AttributeValue(AttributeType.INT, 28))
            bob.add_attribute("role", AttributeValue(AttributeType.STR, "Designer"))

            g.add_node(alice)
            g.add_node(bob)
            g.add_edge(alice, bob, label="supervises")

            svg = self.visualizer.visualize(g, width=800, height=600)
            self.save_svg("blk_03_attributes.svg", svg)

            assert "age" in svg
            assert "role" in svg
            assert "Engineer" in svg
            print("✓ Test 3 PASSED: Nodes with attributes")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 3 FAILED: {e}")
            self.failed += 1

    def test_grid_layout(self):
        """Test 4: Grid layout with 9 nodes."""
        try:
            g = Graph(directed=True, cyclic=True)
            nodes = [Node(f"Item_{i}") for i in range(9)]
            for n in nodes:
                g.add_node(n)
            for i in range(8):
                g.add_edge(nodes[i], nodes[i + 1])

            svg = self.visualizer.visualize(g, width=900, height=900, layout="grid")
            self.save_svg("blk_04_grid.svg", svg)

            assert svg.count("<rect") >= 9
            print("✓ Test 4 PASSED: Grid layout, 9 nodes")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 4 FAILED: {e}")
            self.failed += 1

    def test_force_layout_large(self):
        """Test 5: Force layout with 20 nodes."""
        try:
            g = Graph(directed=True, cyclic=True)
            nodes = [Node(f"Node_{i:02d}") for i in range(20)]
            for n in nodes:
                g.add_node(n)

            random.seed(42)
            for _ in range(30):
                src = random.choice(nodes)
                tgt = random.choice(nodes)
                if src.id != tgt.id:
                    try:
                        g.add_edge(src, tgt)
                    except ValueError:
                        pass

            svg = self.visualizer.visualize(g, width=1000, height=1000, layout="force")
            self.save_svg("blk_05_force_large.svg", svg)

            assert svg.count("<rect") >= 20
            print(f"✓ Test 5 PASSED: Force layout, {len(g.nodes)} nodes, {len(g.edges)} edges")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 5 FAILED: {e}")
            self.failed += 1

    def test_empty_graph(self):
        """Test 6: Empty graph produces valid SVG."""
        try:
            g = Graph(directed=True)
            svg = self.visualizer.visualize(g, width=800, height=600)
            self.save_svg("blk_06_empty.svg", svg)

            assert "<svg" in svg
            assert "</svg>" in svg
            print("✓ Test 6 PASSED: Empty graph")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 6 FAILED: {e}")
            self.failed += 1

    def test_single_node_no_attributes(self):
        """Test 7: Single node with no attributes shows placeholder."""
        try:
            g = Graph(directed=True)
            g.add_node(Node("Isolated"))

            svg = self.visualizer.visualize(g, width=800, height=600)
            self.save_svg("blk_07_single_node.svg", svg)

            assert "Isolated" in svg
            assert "no attributes" in svg
            print("✓ Test 7 PASSED: Single node, no attributes")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 7 FAILED: {e}")
            self.failed += 1

    def test_long_attribute_value_truncated(self):
        """Test 8: Long attribute values are truncated."""
        try:
            g = Graph(directed=True)
            n = Node("LongVal")
            n.add_attribute("desc", AttributeValue(AttributeType.STR, "This is a very long value"))
            g.add_node(n)

            svg = self.visualizer.visualize(g, width=800, height=600)
            self.save_svg("blk_08_truncated.svg", svg)

            assert "…" in svg, "Expected truncation marker"
            print("✓ Test 8 PASSED: Long attribute value truncated")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 8 FAILED: {e}")
            self.failed += 1

    def test_invalid_layout_raises(self):
        """Test 9: Invalid layout raises ValueError."""
        try:
            g = Graph(directed=True)
            g.add_node(Node("A"))
            try:
                self.visualizer.visualize(g, layout="invalid")
                assert False, "Expected ValueError"
            except ValueError:
                pass
            print("✓ Test 9 PASSED: Invalid layout raises ValueError")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 9 FAILED: {e}")
            self.failed += 1

    def test_identifier_and_name(self):
        """Test 10: Plugin identifier and name are correct."""
        try:
            assert self.visualizer.identifier() == "block"
            assert self.visualizer.name() == "Block Visualizer"
            print("✓ Test 10 PASSED: identifier='block', name='Block Visualizer'")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 10 FAILED: {e}")
            self.failed += 1

    # ------------------------------------------------------------------

    def run_all(self):
        print("\n" + "=" * 70)
        print("BLOCK VISUALIZER PLUGIN - TEST SUITE")
        print("=" * 70)

        self.test_directed_graph()
        self.test_undirected_graph()
        self.test_nodes_with_attributes()
        self.test_grid_layout()
        self.test_force_layout_large()
        self.test_empty_graph()
        self.test_single_node_no_attributes()
        self.test_long_attribute_value_truncated()
        self.test_invalid_layout_raises()
        self.test_identifier_and_name()

        print("\n" + "=" * 70)
        print(f"RESULTS: {self.passed} Passed, {self.failed} Failed")
        print("=" * 70)

        if self.failed == 0:
            print("\n✓ ALL TESTS PASSED!")
        else:
            print(f"\n✗ {self.failed} test(s) failed")

        print(f"\nOutput SVGs saved to: {OUTPUT_DIR}")
        for f in sorted(OUTPUT_DIR.glob("blk_*.svg")):
            print(f"  {f.name}")

        return self.failed == 0


def main():
    suite = BlockVisualizerTestSuite()
    success = suite.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())