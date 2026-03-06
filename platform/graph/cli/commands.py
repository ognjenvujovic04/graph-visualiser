from abc import ABC, abstractmethod
from graph.facade.facade import PlatformFacade


class Command(ABC):
    def __init__(self, facade: PlatformFacade):
        self.facade = facade

    @abstractmethod
    def execute(self) -> str:
        pass


class CreateNodeCommand(Command):
    def __init__(self, facade: PlatformFacade, node_id: str, attributes: dict):
        super().__init__(facade)
        self.node_id = node_id
        self.attributes = attributes

    def execute(self) -> str:
        self.facade.add_node(self.node_id, **self.attributes)
        attrs = ", ".join(f"{k}={v}" for k, v in self.attributes.items())
        return f"✓ Node '{self.node_id}' created." + (f" [{attrs}]" if attrs else "")


class EditNodeCommand(Command):
    def __init__(self, facade: PlatformFacade, node_id: str, attributes: dict):
        super().__init__(facade)
        self.node_id = node_id
        self.attributes = attributes

    def execute(self) -> str:
        self.facade.edit_node(self.node_id, **self.attributes)
        attrs = ", ".join(f"{k}={v}" for k, v in self.attributes.items())
        return f"✓ Node '{self.node_id}' updated. [{attrs}]"


class DeleteNodeCommand(Command):
    def __init__(self, facade: PlatformFacade, node_id: str):
        super().__init__(facade)
        self.node_id = node_id

    def execute(self) -> str:
        self.facade.remove_node(self.node_id)
        return f"✓ Node '{self.node_id}' deleted."


class CreateEdgeCommand(Command):
    def __init__(self, facade: PlatformFacade, source_id: str, target_id: str,
                 label: str = "", attributes: dict = None):
        super().__init__(facade)
        self.source_id = source_id
        self.target_id = target_id
        self.label = label
        self.attributes = attributes or {}

    def execute(self) -> str:
        edge = self.facade.add_edge(self.source_id, self.target_id, self.label)
        if self.attributes:
            self.facade.edit_edge(edge.id, **self.attributes)
        return f"✓ Edge '{edge.id}' created: {self.source_id} -> {self.target_id}."


class EditEdgeCommand(Command):
    def __init__(self, facade: PlatformFacade, edge_id: str, attributes: dict):
        super().__init__(facade)
        self.edge_id = edge_id
        self.attributes = attributes

    def execute(self) -> str:
        self.facade.edit_edge(self.edge_id, **self.attributes)
        attrs = ", ".join(f"{k}={v}" for k, v in self.attributes.items())
        return f"✓ Edge '{self.edge_id}' updated. [{attrs}]"


class DeleteEdgeCommand(Command):
    def __init__(self, facade: PlatformFacade, edge_id: str):
        super().__init__(facade)
        self.edge_id = edge_id

    def execute(self) -> str:
        self.facade.remove_edge(self.edge_id)
        return f"✓ Edge '{self.edge_id}' deleted."


class SearchCommand(Command):
    def __init__(self, facade: PlatformFacade, text: str):
        super().__init__(facade)
        self.text = text

    def execute(self) -> str:
        graph = self.facade.search(self.text)
        return f"✓ Search '{self.text}': {len(graph.nodes)} nodes, {len(graph.edges)} edges."


class FilterCommand(Command):
    def __init__(self, facade: PlatformFacade, expr: str):
        super().__init__(facade)
        self.expr = expr

    def execute(self) -> str:
        graph = self.facade.filter(self.expr)
        return f"✓ Filter '{self.expr}': {len(graph.nodes)} nodes, {len(graph.edges)} edges."


class ClearCommand(Command):
    def __init__(self, facade: PlatformFacade):
        super().__init__(facade)

    def execute(self) -> str:
        self.facade.clear_graph()
        return "✓ Graph cleared."


class ResetCommand(Command):
    def __init__(self, facade: PlatformFacade):
        super().__init__(facade)

    def execute(self) -> str:
        graph = self.facade.reset_graph()
        return f"✓ Graph reset to original: {len(graph.nodes)} nodes, {len(graph.edges)} edges."