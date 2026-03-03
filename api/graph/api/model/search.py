from typing import List, Optional
from .graph import Graph
from .node import Node


class SearchOperation:
    """
    Performs a search operation on a graph by finding nodes that contain
    a search text in either attribute names or attribute values.
    
    - Search input accepts arbitrary text (query)
    - Forms a subgraph of current graph whose nodes contain the search text
    - Searches attribute names and values (contains operation)
    """
    
    def __init__(self, search_text: str):
        if not isinstance(search_text, str):
            raise TypeError("search_text must be a string")
        if not search_text.strip():
            raise ValueError("search_text cannot be empty")
        
        self.search_text = search_text.lower()  # Case-insensitive search
    
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
            # Check if node ID contains search text
            if self.search_text in node.id.lower():
                matching_nodes.append(node)
                continue
            
            # Check if any attribute name or value contains search text
            if self._node_has_matching_attribute(node):
                matching_nodes.append(node)
        
        return matching_nodes
    
    def _node_has_matching_attribute(self, node: Node) -> bool:
        for attr_name, attr_value in node.attributes.items():
            # Check attribute name
            if self.search_text in attr_name.lower():
                return True
            
            # Check attribute value (convert to string for comparison)
            attr_value_str = str(attr_value).lower()
            if self.search_text in attr_value_str:
                return True
        
        return False
    
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
        return f"SearchOperation('{self.search_text}')"
    
    def __repr__(self) -> str:
        return f"SearchOperation(search_text='{self.search_text}')"
