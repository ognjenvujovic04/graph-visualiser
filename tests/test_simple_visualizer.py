from pathlib import Path
from graph.api.model.graph import Graph
from graph.api.model.node import Node
from graph.api.model.attributes import AttributeValue, AttributeType
from graph.simple_plugin.visualizer import SimpleVisualizer


OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


class SimpleVisualizerTestSuite:
    """Simple test suite for visualizer plugin."""
    
    def __init__(self):
        self.visualizer = SimpleVisualizer()
        self.passed = 0
        self.failed = 0
    
    def save_html(self, filename: str, html: str) -> str:
        """Save HTML to output folder and return path."""
        filepath = OUTPUT_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return str(filepath)

    def assert_valid_html(self, html: str) -> None:
        """Basic checks proving renderer returns full HTML visualization content."""
        assert isinstance(html, str)
        assert "<style>" in html
        assert "id=\"graph-container\"" in html
        assert "id=\"nodes-data\"" in html
        assert "id=\"edges-data\"" in html
        assert "https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js" in html
        assert "function render()" in html
    
    def test_directed_graph(self):
        """Test 1: Simple directed graph with 3 nodes (dark theme)."""
        try:
            graph = Graph(directed=True, cyclic=True)
            
            nodes = [Node(name) for name in ["Alice", "Bob", "Charlie"]]
            for node in nodes:
                graph.add_node(node)
            
            graph.add_edge(nodes[0], nodes[1], label="knows")
            graph.add_edge(nodes[1], nodes[2], label="works_with")
            graph.add_edge(nodes[2], nodes[0], label="respects")
            
            html = self.visualizer.visualize(graph, width=800, height=600, theme="dark")
            self.assert_valid_html(html)
            self.save_html("01_directed_graph.html", html)
            
            print(f"✓ Test 1 PASSED: Directed graph [DARK] ({len(graph.nodes)} nodes, {len(graph.edges)} edges)")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 1 FAILED: {e}")
            self.failed += 1
    
    def test_undirected_graph(self):
        """Test 2: Undirected graph with force layout (light theme)."""
        try:
            graph = Graph(directed=False, cyclic=True)
            
            nodes = [Node(f"N{i}") for i in range(5)]
            for node in nodes:
                graph.add_node(node)
            
            for i in range(5):
                graph.add_edge(nodes[i], nodes[(i + 1) % 5])
            
            html = self.visualizer.visualize(graph, width=800, height=600, theme="light")
            self.assert_valid_html(html)
            self.save_html("02_undirected_graph.html", html)
            
            print(f"✓ Test 2 PASSED: Undirected graph [LIGHT] ({len(graph.nodes)} nodes)")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 2 FAILED: {e}")
            self.failed += 1
    
    def test_graph_with_attributes(self):
        """Test 3: Graph with node attributes."""
        try:
            graph = Graph(directed=True, cyclic=False)
            
            # Create nodes with attributes
            alice = Node("Alice")
            alice.add_attribute("age", AttributeValue(AttributeType.INT, 30))
            alice.add_attribute("role", AttributeValue(AttributeType.STR, "Engineer"))
            
            bob = Node("Bob")
            bob.add_attribute("age", AttributeValue(AttributeType.INT, 28))
            bob.add_attribute("role", AttributeValue(AttributeType.STR, "Designer"))
            
            for node in [alice, bob]:
                graph.add_node(node)
            
            graph.add_edge(alice, bob, label="supervises")
            
            html = self.visualizer.visualize(graph, width=800, height=600, theme="dark")
            self.assert_valid_html(html)
            self.save_html("03_with_attributes.html", html)
            
            print(f"✓ Test 3 PASSED: Graph with attributes [DARK] (nodes have properties)")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 3 FAILED: {e}")
            self.failed += 1
    
    def test_many_nodes_force(self):
        """Test 4: Force layout with 9 nodes."""
        try:
            graph = Graph(directed=True, cyclic=True)
            
            nodes = [Node(f"Item_{i}") for i in range(9)]
            for node in nodes:
                graph.add_node(node)
            
            for i in range(8):
                graph.add_edge(nodes[i], nodes[i + 1])
            
            html = self.visualizer.visualize(
                graph, 
                width=900, 
                height=900, 
                node_radius=25,
                theme="light"
            )
            self.assert_valid_html(html)
            self.save_html("04_many_nodes_force.html", html)
            
            print(f"✓ Test 4 PASSED: Force layout [LIGHT] with nodes ({len(graph.nodes)} nodes, {len(graph.edges)} edges)")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 4 FAILED: {e}")
            self.failed += 1
    
    def test_force_layout_large(self):
        """Test 5: Force-directed layout with 20 nodes."""
        try:
            import random
            
            graph = Graph(directed=True, cyclic=True)
            
            nodes = [Node(f"Node_{i:02d}") for i in range(20)]
            for node in nodes:
                graph.add_node(node)
            
            random.seed(42)
            for _ in range(30):
                src = random.choice(nodes)
                tgt = random.choice(nodes)
                if src.id != tgt.id:
                    try:
                        graph.add_edge(src, tgt)
                    except ValueError:
                        pass
            
            html = self.visualizer.visualize(
                graph,
                width=1000,
                height=1000,
                node_radius=20,
                layout="force",
                theme="dark"
            )
            self.assert_valid_html(html)
            self.save_html("05_force_layout_large.html", html)
            
            print(f"✓ Test 5 PASSED: Force layout [DARK] ({len(graph.nodes)} nodes, {len(graph.edges)} edges)")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 5 FAILED: {e}")
            self.failed += 1
    
    def test_empty_graph(self):
        """Test 6: Empty graph (light theme)."""
        try:
            graph = Graph(directed=True)
            
            html = self.visualizer.visualize(graph, width=800, height=600, theme="light")
            self.assert_valid_html(html)
            self.save_html("06_empty_graph.html", html)
            
            print(f"✓ Test 6 PASSED: Empty graph [LIGHT] handled correctly")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 6 FAILED: {e}")
            self.failed += 1
    
    def test_single_node(self):
        """Test 7: Single node graph (dark theme)."""
        try:
            graph = Graph(directed=True)
            graph.add_node(Node("Isolated"))
            
            html = self.visualizer.visualize(graph, width=800, height=600, theme="dark")
            self.assert_valid_html(html)
            self.save_html("07_single_node.html", html)
            
            print(f"✓ Test 7 PASSED: Single node graph [DARK]")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 7 FAILED: {e}")
            self.failed += 1
    
    def run_all(self):
        """Run all tests."""
        print("\n" + "="*70)
        print("SIMPLE VISUALIZER PLUGIN - TEST SUITE")
        print("="*70)
        
        self.test_directed_graph()
        self.test_undirected_graph()
        self.test_graph_with_attributes()
        self.test_many_nodes_force()
        self.test_force_layout_large()
        self.test_empty_graph()
        self.test_single_node()
        
        print("\n" + "="*70)
        print(f"RESULTS: {self.passed} Passed, {self.failed} Failed")
        print("="*70)
        print(f"\nOutput files saved to: {OUTPUT_DIR}")
        print("\nGenerated HTML files:")
        for i, file in enumerate(sorted(OUTPUT_DIR.glob("*.html")), 1):
            print(f"  {i}. {file.name}")
        
        if self.failed == 0:
            print("\n✓ ALL TESTS PASSED!")
        else:
            print(f"\n✗ {self.failed} test(s) failed")
        
        return self.failed == 0


def main():
    """Main entry point."""
    suite = SimpleVisualizerTestSuite()
    success = suite.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
