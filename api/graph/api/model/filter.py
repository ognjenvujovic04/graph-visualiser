import re
from typing import List
from enum import Enum
from .graph import Graph
from .node import Node
from .attributes import AttributeValue


class FilterOperator(Enum):
    """Supported filter comparison operators."""
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="
    
    @classmethod
    def from_string(cls, op_str: str) -> 'FilterOperator':
        for op in cls:
            if op.value == op_str:
                return op
        raise ValueError(f"Unknown operator: {op_str}. Valid operators: {', '.join(op.value for op in cls)}")


class FilterExpression:    
    # Regex pattern to parse filter expression
    FILTER_PATTERN = r'^(\w+)\s*(==|!=|>=|<=|>|<)\s*(.+)$'
    
    def __init__(self, attribute_name: str, operator: FilterOperator, value: str):
        if not isinstance(attribute_name, str) or not attribute_name.strip():
            raise ValueError("attribute_name must be a non-empty string")
        if not isinstance(operator, FilterOperator):
            raise TypeError("operator must be a FilterOperator instance")
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        
        self.attribute_name = attribute_name.strip()
        self.operator = operator
        self.value_str = value.strip()
    
    @classmethod
    def parse(cls, filter_string: str) -> 'FilterExpression':
        if not isinstance(filter_string, str):
            raise TypeError("filter_string must be a string")
        
        match = re.match(cls.FILTER_PATTERN, filter_string)
        if not match:
            raise ValueError(
                f"Invalid filter format: '{filter_string}'. "
                f"Expected format: <attribute_name> <operator> <value>. "
                f"Valid operators: ==, !=, >, >=, <, <="
            )
        
        attribute_name, operator_str, value = match.groups()
        operator = FilterOperator.from_string(operator_str)
        
        return cls(attribute_name, operator, value)
    
    def evaluate(self, node: Node) -> bool:
        # Get the attribute from the node
        attr_value = node.get_attribute(self.attribute_name)
        
        # If attribute doesn't exist, node doesn't match
        if attr_value is None:
            return False
        
        # Try to convert and compare values
        try:
            return self._compare(attr_value, self.value_str)
        except (TypeError, ValueError) as e:
            # Type mismatch - node doesn't match
            return False
    
    def _compare(self, attr_value: AttributeValue, filter_value: str) -> bool:
        # Convert filter value to match the type of attribute value
        actual_value = attr_value.value
        actual_type = type(actual_value)
        
        # Convert filter value to appropriate type
        if actual_type == int:
            try:
                filter_value_converted = int(filter_value)
            except ValueError:
                raise ValueError(
                    f"Cannot convert filter value '{filter_value}' to int. "
                    f"Attribute '{self.attribute_name}' is of type int."
                )
        elif actual_type == float:
            try:
                filter_value_converted = float(filter_value)
            except ValueError:
                raise ValueError(
                    f"Cannot convert filter value '{filter_value}' to float. "
                    f"Attribute '{self.attribute_name}' is of type float."
                )
        elif actual_type == bool:
            if filter_value.lower() in ('true', '1', 'yes', 'on'):
                filter_value_converted = True
            elif filter_value.lower() in ('false', '0', 'no', 'off'):
                filter_value_converted = False
            else:
                raise ValueError(
                    f"Cannot convert filter value '{filter_value}' to bool. "
                    f"Valid values: true/false/1/0/yes/no/on/off"
                )
        else:
            # String comparison - no conversion needed
            filter_value_converted = filter_value
        
        # Perform comparison based on operator
        if self.operator == FilterOperator.EQUAL:
            return actual_value == filter_value_converted
        elif self.operator == FilterOperator.NOT_EQUAL:
            return actual_value != filter_value_converted
        elif self.operator == FilterOperator.GREATER:
            return actual_value > filter_value_converted
        elif self.operator == FilterOperator.GREATER_EQUAL:
            return actual_value >= filter_value_converted
        elif self.operator == FilterOperator.LESS:
            return actual_value < filter_value_converted
        elif self.operator == FilterOperator.LESS_EQUAL:
            return actual_value <= filter_value_converted
        else:
            raise ValueError(f"Unknown operator: {self.operator}")
    
    def __str__(self) -> str:
        return f"{self.attribute_name} {self.operator.value} {self.value_str}"
    
    def __repr__(self) -> str:
        return f"FilterExpression(attribute='{self.attribute_name}', operator={self.operator.value}, value='{self.value_str}')"


class FilterOperation:
    """
    Performs a filter operation on a graph by finding nodes that match
    the specified filter criteria.
    
    - Filter format: attribute_name comparator value
    - Comparators: ==, >, >=, <, <=, !=
    - Forms a subgraph of current graph whose nodes satisfy the filter
    - Shows error if value is of wrong type
    - Can be applied successively
    """
    
    def __init__(self, filter_expr: FilterExpression):
        if isinstance(filter_expr, str):
            self.filter_expr = FilterExpression.parse(filter_expr)
        elif isinstance(filter_expr, FilterExpression):
            self.filter_expr = filter_expr
        else:
            raise TypeError("filter_expr must be FilterExpression or string")
    
    def execute(self, graph: Graph) -> Graph:
        if not isinstance(graph, Graph):
            raise TypeError("graph must be a Graph instance")
        
        # Find matching nodes
        matching_nodes = self._find_matching_nodes(graph)
        
        # Create subgraph with matching nodes
        return self._create_subgraph(graph, matching_nodes)
    
    def _find_matching_nodes(self, graph: Graph) -> List[Node]:
        matching_nodes = []
        
        for node in graph.nodes:
            if self.filter_expr.evaluate(node):
                matching_nodes.append(node)
        
        return matching_nodes
    
    def _create_subgraph(self, original_graph: Graph, matching_nodes: List[Node]) -> Graph:
        # Create new graph with same properties as original
        subgraph = Graph(directed=original_graph.directed, cyclic=original_graph.cyclic)
        
        # Create mapping of node IDs for easy lookup
        matching_node_ids = {node.id for node in matching_nodes}
        
        # Add all matching nodes to subgraph
        for node in matching_nodes:
            # Create a copy of the node to avoid modifying original
            node_copy = Node(node.id)
            for attr_name, attr_value in node.attributes.items():
                node_copy.add_attribute(attr_name, attr_value)
            subgraph.add_node(node_copy)
        
        # Add edges that connect nodes in the subgraph
        for edge in original_graph.edges:
            if edge.source.id in matching_node_ids and edge.target.id in matching_node_ids:
                source_node = subgraph.get_node(edge.source.id)
                target_node = subgraph.get_node(edge.target.id)
                if source_node and target_node:
                    subgraph.add_edge(source_node, target_node, edge.label)
        
        return subgraph
    
    def __str__(self) -> str:
        return f"FilterOperation({self.filter_expr})"
    
    def __repr__(self) -> str:
        return f"FilterOperation(filter_expr={repr(self.filter_expr)})"
