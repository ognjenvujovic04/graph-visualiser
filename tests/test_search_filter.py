import sys
from pathlib import Path

# Add the api directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from graph.api.model import (
    Graph,
    Node,
    AttributeValue,
    AttributeType,
    SearchOperation,
    FilterOperation,
    FilterExpression,
    FilterOperator,
)


class SearchFilterTestSuite:
    """Test suite for Search and Filter operations."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
    
    def create_basic_graph(self):
        """Create a basic test graph."""
        graph = Graph(directed=True, cyclic=True)
        
        # Add nodes
        alice = Node("n1")
        alice.add_attribute("name", AttributeValue(AttributeType.STR, "Alice"))
        alice.add_attribute("age", AttributeValue(AttributeType.INT, 30))
        
        bob = Node("n2")
        bob.add_attribute("name", AttributeValue(AttributeType.STR, "Bob"))
        bob.add_attribute("age", AttributeValue(AttributeType.INT, 25))
        
        charlie = Node("n3")
        charlie.add_attribute("name", AttributeValue(AttributeType.STR, "Charlie"))
        charlie.add_attribute("age", AttributeValue(AttributeType.INT, 35))
        
        graph.add_node(alice)
        graph.add_node(bob)
        graph.add_node(charlie)
        
        # Add edges
        graph.add_edge(alice, bob, "knows")
        graph.add_edge(bob, charlie, "knows")
        
        return graph
    
    def test_search_by_attribute_value(self):
        """Test 1: Search finds nodes by attribute value."""
        try:
            graph = self.create_basic_graph()
            search = SearchOperation("alice")
            result = search.execute(graph)
            
            assert len(result.nodes) == 1, f"Expected 1 node, got {len(result.nodes)}"
            assert result.nodes[0].id == "n1", f"Expected node n1, got {result.nodes[0].id}"
            
            print(f"✓ Test 1 PASSED: Search finds nodes by attribute value")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 1 FAILED: {e}")
            self.failed += 1
    
    def test_search_by_attribute_name(self):
        """Test 2: Search finds nodes by attribute name."""
        try:
            graph = self.create_basic_graph()
            search = SearchOperation("age")
            result = search.execute(graph)
            
            assert len(result.nodes) == 3, f"Expected 3 nodes, got {len(result.nodes)}"
            
            print(f"✓ Test 2 PASSED: Search finds nodes by attribute name")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 2 FAILED: {e}")
            self.failed += 1
    
    def test_search_by_node_id(self):
        """Test 3: Search finds nodes by ID."""
        try:
            graph = self.create_basic_graph()
            search = SearchOperation("n2")
            result = search.execute(graph)
            
            assert len(result.nodes) == 1, f"Expected 1 node, got {len(result.nodes)}"
            assert result.nodes[0].id == "n2", f"Expected node n2, got {result.nodes[0].id}"
            
            print(f"✓ Test 3 PASSED: Search finds nodes by ID")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 3 FAILED: {e}")
            self.failed += 1
    
    def test_search_case_insensitive(self):
        """Test 4: Search is case-insensitive."""
        try:
            graph = self.create_basic_graph()
            search = SearchOperation("ALICE")
            result = search.execute(graph)
            
            assert len(result.nodes) == 1, f"Expected 1 node, got {len(result.nodes)}"
            assert result.nodes[0].id == "n1", f"Expected node n1, got {result.nodes[0].id}"
            
            print(f"✓ Test 4 PASSED: Search is case-insensitive")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 4 FAILED: {e}")
            self.failed += 1
    
    def test_search_preserves_edges(self):
        """Test 5: Search preserves edges between matching nodes."""
        try:
            graph = self.create_basic_graph()
            search = SearchOperation("age")
            result = search.execute(graph)
            
            assert len(result.nodes) == 3, f"Expected 3 nodes, got {len(result.nodes)}"
            assert len(result.edges) == 2, f"Expected 2 edges, got {len(result.edges)}"
            
            print(f"✓ Test 5 PASSED: Search preserves edges between matching nodes")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 5 FAILED: {e}")
            self.failed += 1
    
    def test_search_no_results(self):
        """Test 6: Search with no matching nodes returns empty graph."""
        try:
            graph = self.create_basic_graph()
            search = SearchOperation("nonexistent")
            result = search.execute(graph)
            
            assert len(result.nodes) == 0, f"Expected 0 nodes, got {len(result.nodes)}"
            assert len(result.edges) == 0, f"Expected 0 edges, got {len(result.edges)}"
            
            print(f"✓ Test 6 PASSED: Search with no results returns empty graph")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 6 FAILED: {e}")
            self.failed += 1
    
    def test_search_empty_string_error(self):
        """Test 7: Search with empty string raises ValueError."""
        try:
            try:
                SearchOperation("")
                assert False, "Expected ValueError for empty search text"
            except ValueError:
                pass  # Expected
            
            print(f"✓ Test 7 PASSED: Search with empty string raises ValueError")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 7 FAILED: {e}")
            self.failed += 1
    
    def test_filter_parse_valid(self):
        """Test 8: Filter expression parsing works correctly."""
        try:
            expr = FilterExpression.parse("age >= 25")
            
            assert expr.attribute_name == "age", f"Expected 'age', got {expr.attribute_name}"
            assert expr.operator == FilterOperator.GREATER_EQUAL, f"Expected >=, got {expr.operator}"
            assert expr.value_str == "25", f"Expected '25', got {expr.value_str}"
            
            print(f"✓ Test 8 PASSED: Filter expression parsing works correctly")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 8 FAILED: {e}")
            self.failed += 1
    
    def test_filter_parse_invalid(self):
        """Test 9: Invalid filter format raises ValueError."""
        try:
            try:
                FilterExpression.parse("age 25")  # Missing operator
                assert False, "Expected ValueError for invalid format"
            except ValueError:
                pass  # Expected
            
            print(f"✓ Test 9 PASSED: Invalid filter format raises ValueError")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 9 FAILED: {e}")
            self.failed += 1
    
    def test_filter_equal_operator(self):
        """Test 10: Filter with == operator works correctly."""
        try:
            node = Node("n1")
            node.add_attribute("age", AttributeValue(AttributeType.INT, 30))
            
            expr = FilterExpression.parse("age == 30")
            assert expr.evaluate(node) is True, "Expected node to match age == 30"
            
            expr = FilterExpression.parse("age == 25")
            assert expr.evaluate(node) is False, "Expected node to not match age == 25"
            
            print(f"✓ Test 10 PASSED: Filter with == operator works correctly")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 10 FAILED: {e}")
            self.failed += 1
    
    def test_filter_greater_operator(self):
        """Test 11: Filter with > operator works correctly."""
        try:
            node = Node("n1")
            node.add_attribute("age", AttributeValue(AttributeType.INT, 30))
            
            expr = FilterExpression.parse("age > 25")
            assert expr.evaluate(node) is True, "Expected node to match age > 25"
            
            expr = FilterExpression.parse("age > 30")
            assert expr.evaluate(node) is False, "Expected node to not match age > 30"
            
            print(f"✓ Test 11 PASSED: Filter with > operator works correctly")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 11 FAILED: {e}")
            self.failed += 1
    
    def test_filter_less_operator(self):
        """Test 12: Filter with < operator works correctly."""
        try:
            node = Node("n1")
            node.add_attribute("age", AttributeValue(AttributeType.INT, 30))
            
            expr = FilterExpression.parse("age < 35")
            assert expr.evaluate(node) is True, "Expected node to match age < 35"
            
            expr = FilterExpression.parse("age < 30")
            assert expr.evaluate(node) is False, "Expected node to not match age < 30"
            
            print(f"✓ Test 12 PASSED: Filter with < operator works correctly")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 12 FAILED: {e}")
            self.failed += 1
    
    def test_filter_not_equal_operator(self):
        """Test 13: Filter with != operator works correctly."""
        try:
            node = Node("n1")
            node.add_attribute("age", AttributeValue(AttributeType.INT, 30))
            
            expr = FilterExpression.parse("age != 25")
            assert expr.evaluate(node) is True, "Expected node to match age != 25"
            
            expr = FilterExpression.parse("age != 30")
            assert expr.evaluate(node) is False, "Expected node to not match age != 30"
            
            print(f"✓ Test 13 PASSED: Filter with != operator works correctly")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 13 FAILED: {e}")
            self.failed += 1
    
    def test_filter_string_attribute(self):
        """Test 14: Filter on string attributes works correctly."""
        try:
            node = Node("n1")
            node.add_attribute("name", AttributeValue(AttributeType.STR, "Alice"))
            
            expr = FilterExpression.parse("name == Alice")
            assert expr.evaluate(node) is True, "Expected node to match name == Alice"
            
            expr = FilterExpression.parse("name == Bob")
            assert expr.evaluate(node) is False, "Expected node to not match name == Bob"
            
            print(f"✓ Test 14 PASSED: Filter on string attributes works correctly")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 14 FAILED: {e}")
            self.failed += 1
    
    def test_filter_missing_attribute(self):
        """Test 15: Filter on missing attribute returns False."""
        try:
            node = Node("n1")
            node.add_attribute("age", AttributeValue(AttributeType.INT, 30))
            
            expr = FilterExpression.parse("missing == value")
            assert expr.evaluate(node) is False, "Expected False for missing attribute"
            
            print(f"✓ Test 15 PASSED: Filter on missing attribute returns False")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 15 FAILED: {e}")
            self.failed += 1
    
    def test_filter_type_mismatch(self):
        """Test 16: Filter handles type mismatch gracefully."""
        try:
            node = Node("n1")
            node.add_attribute("age", AttributeValue(AttributeType.INT, 30))
            
            expr = FilterExpression.parse("age > abc")
            assert expr.evaluate(node) is False, "Expected False for type mismatch"
            
            print(f"✓ Test 16 PASSED: Filter handles type mismatch gracefully")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 16 FAILED: {e}")
            self.failed += 1
    
    def test_filter_operation_greater_than(self):
        """Test 17: FilterOperation with > operator."""
        try:
            graph = self.create_basic_graph()
            filter_op = FilterOperation("age > 25")
            result = filter_op.execute(graph)
            
            assert len(result.nodes) == 2, f"Expected 2 nodes, got {len(result.nodes)}"
            node_ids = {node.id for node in result.nodes}
            assert node_ids == {"n1", "n3"}, f"Expected nodes n1 and n3, got {node_ids}"
            
            print(f"✓ Test 17 PASSED: FilterOperation with > operator")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 17 FAILED: {e}")
            self.failed += 1
    
    def test_filter_operation_equal(self):
        """Test 18: FilterOperation with == operator."""
        try:
            graph = self.create_basic_graph()
            filter_op = FilterOperation("age == 30")
            result = filter_op.execute(graph)
            
            assert len(result.nodes) == 1, f"Expected 1 node, got {len(result.nodes)}"
            assert result.nodes[0].id == "n1", f"Expected node n1, got {result.nodes[0].id}"
            
            print(f"✓ Test 18 PASSED: FilterOperation with == operator")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 18 FAILED: {e}")
            self.failed += 1
    
    def test_filter_operation_preserves_edges(self):
        """Test 19: FilterOperation preserves edges between matching nodes."""
        try:
            graph = self.create_basic_graph()
            filter_op = FilterOperation("age >= 30")
            result = filter_op.execute(graph)
            
            assert len(result.nodes) == 2, f"Expected 2 nodes, got {len(result.nodes)}"
            assert len(result.edges) == 0, f"Expected 0 edges, got {len(result.edges)}"
            
            print(f"✓ Test 19 PASSED: FilterOperation preserves edges correctly")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 19 FAILED: {e}")
            self.failed += 1
    
    def test_filter_operation_no_results(self):
        """Test 20: FilterOperation with no matching nodes."""
        try:
            graph = self.create_basic_graph()
            filter_op = FilterOperation("age > 100")
            result = filter_op.execute(graph)
            
            assert len(result.nodes) == 0, f"Expected 0 nodes, got {len(result.nodes)}"
            assert len(result.edges) == 0, f"Expected 0 edges, got {len(result.edges)}"
            
            print(f"✓ Test 20 PASSED: FilterOperation with no matching nodes")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 20 FAILED: {e}")
            self.failed += 1
    
    def test_graph_search_method(self):
        """Test 21: Graph.search() convenience method."""
        try:
            graph = self.create_basic_graph()
            result = graph.search("Alice")
            
            assert len(result.nodes) == 1, f"Expected 1 node, got {len(result.nodes)}"
            assert result.nodes[0].id == "n1", f"Expected node n1, got {result.nodes[0].id}"
            
            print(f"✓ Test 21 PASSED: Graph.search() convenience method")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 21 FAILED: {e}")
            self.failed += 1
    
    def test_graph_filter_method(self):
        """Test 22: Graph.filter() convenience method."""
        try:
            graph = self.create_basic_graph()
            result = graph.filter("age >= 30")
            
            assert len(result.nodes) == 2, f"Expected 2 nodes, got {len(result.nodes)}"
            
            print(f"✓ Test 22 PASSED: Graph.filter() convenience method")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 22 FAILED: {e}")
            self.failed += 1
    
    def test_successive_operations(self):
        """Test 23: Successive search and filter operations."""
        try:
            graph = self.create_basic_graph()
            
            # Search for 'age' attribute (all nodes have it)
            result = graph.search("age")
            assert len(result.nodes) == 3, f"Expected 3 nodes after search, got {len(result.nodes)}"
            
            # Then filter (only nodes with age >= 30)
            result = result.filter("age >= 30")
            assert len(result.nodes) == 2, f"Expected 2 nodes after filter, got {len(result.nodes)}"
            node_ids = {node.id for node in result.nodes}
            assert node_ids == {"n1", "n3"}, f"Expected nodes n1 and n3, got {node_ids}"
            
            print(f"✓ Test 23 PASSED: Successive search and filter operations")
            self.passed += 1
        except Exception as e:
            print(f"✗ Test 23 FAILED: {e}")
            self.failed += 1
    
    def run_all(self):
        """Run all tests."""
        print("\n" + "="*70)
        print("SEARCH & FILTER OPERATIONS - TEST SUITE")
        print("="*70)
        
        self.test_search_by_attribute_value()
        self.test_search_by_attribute_name()
        self.test_search_by_node_id()
        self.test_search_case_insensitive()
        self.test_search_preserves_edges()
        self.test_search_no_results()
        self.test_search_empty_string_error()
        self.test_filter_parse_valid()
        self.test_filter_parse_invalid()
        self.test_filter_equal_operator()
        self.test_filter_greater_operator()
        self.test_filter_less_operator()
        self.test_filter_not_equal_operator()
        self.test_filter_string_attribute()
        self.test_filter_missing_attribute()
        self.test_filter_type_mismatch()
        self.test_filter_operation_greater_than()
        self.test_filter_operation_equal()
        self.test_filter_operation_preserves_edges()
        self.test_filter_operation_no_results()
        self.test_graph_search_method()
        self.test_graph_filter_method()
        self.test_successive_operations()
        
        print("\n" + "="*70)
        print(f"RESULTS: {self.passed} Passed, {self.failed} Failed")
        print("="*70)
        
        if self.failed == 0:
            print("\n✓ ALL TESTS PASSED!")
        else:
            print(f"\n✗ {self.failed} test(s) failed")
        
        return self.failed == 0


def main():
    """Main entry point."""
    suite = SearchFilterTestSuite()
    success = suite.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
