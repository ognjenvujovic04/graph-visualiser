import sys
from pathlib import Path
from graph.api.model.graph import Graph, Node
from graph.api.model.attributes import AttributeValue, AttributeType
from graph.workspaces.workspace_manager import WorkspaceManager
from graph.api.services.plugin import DataSourcePlugin

OUTPUT_DIR = Path(__file__).parent / "output_workspace"
OUTPUT_DIR.mkdir(exist_ok=True)

# Dummy DataSourcePlugin za test Workspace
class DummyPlugin(DataSourcePlugin):
    def name(self) -> str:
        return "Dummy Plugin"

    def identifier(self) -> str:
        return "dummy"

    def load(self, **kwargs) -> Graph:
        g = Graph(directed=True, cyclic=True)
        n1 = Node("A")
        n1.add_attribute("value", AttributeValue(AttributeType.INT, 10))
        n2 = Node("B")
        n2.add_attribute("value", AttributeValue(AttributeType.INT, 20))
        n3 = Node("C")
        n3.add_attribute("value", AttributeValue(AttributeType.INT, 30))

        g.add_node(n1)
        g.add_node(n2)
        g.add_node(n3)

        g.add_edge(n1, n2, "edge1")
        g.add_edge(n2, n3, "edge2")
        return g

class WorkspaceTestSuite:
    """Test suite for WorkspaceManager functionality."""

    def __init__(self):
        self.manager = WorkspaceManager()
        self.passed = 0
        self.failed = 0

    def test_create_workspaces(self):
        """Test 1: Create multiple workspaces from plugin."""
        try:
            plugin = DummyPlugin()
            ws1 = self.manager.create_workspace_from_plugin(plugin, "WS1")
            ws2 = self.manager.create_workspace_from_plugin(plugin, "WS2")

            assert "WS1" in self.manager.list_workspaces()
            assert "WS2" in self.manager.list_workspaces()

            print(f"✓ Test 1 PASSED: Create multiple workspaces")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 1 FAILED: {e}")
            self.failed += 1

    def test_switch_workspace(self):
        """Test 2: Switch active workspace."""
        try:
            self.manager.switch_workspace("WS1")
            active = self.manager.get_active_workspace()
            assert active.name == "WS1"
            self.manager.switch_workspace("WS2")
            active = self.manager.get_active_workspace()
            assert active.name == "WS2"

            print(f"✓ Test 2 PASSED: Switch active workspace")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 2 FAILED: {e}")
            self.failed += 1

    def test_active_graph_operations(self):
        """Test 3: Apply dummy filter/search and reset."""
        try:
            self.manager.switch_workspace("WS1")
            ws = self.manager.get_active_workspace()

            # Apply filter/search (dummy, returns same graph)
            ws.apply_filter("value >= 0")
            ws.apply_search("A")
            graph_before_reset = ws.get_active_graph()

            ws.reset_active_graph()
            graph_after_reset = ws.get_active_graph()

            assert len(graph_before_reset.nodes) == len(graph_after_reset.nodes)
            assert len(graph_before_reset.edges) == len(graph_after_reset.edges)

            print(f"✓ Test 3 PASSED: Active graph operations and reset")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 3 FAILED: {e}")
            self.failed += 1

    def run_all(self):
        print("\n" + "="*70)
        print("WORKSPACE MANAGER - TEST SUITE")
        print("="*70)

        self.test_create_workspaces()
        self.test_switch_workspace()
        self.test_active_graph_operations()

        print("\n" + "="*70)
        print(f"RESULTS: {self.passed} Passed, {self.failed} Failed")
        print("="*70)
        if self.failed == 0:
            print("\n✓ ALL TESTS PASSED!")
        else:
            print(f"\n✗ {self.failed} test(s) failed")

        return self.failed == 0


def main():
    suite = WorkspaceTestSuite()
    success = suite.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())