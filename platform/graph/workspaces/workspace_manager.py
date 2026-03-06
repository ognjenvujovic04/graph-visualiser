from typing import Dict, Optional
from graph.api.model.graph import Graph
from graph.api.services.plugin import DataSourcePlugin
from .workspace import Workspace

class WorkspaceManager:
    """
    Upravljanje vise workspace-ova.
    Integracija sa plugin sistemom (DataSourcePlugin).
    """
    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}
        self.active_workspace_name: Optional[str] = None

    def create_workspace(self, name: str, source_plugin: DataSourcePlugin, graph: Graph) -> Workspace:
        if name in self.workspaces:
            raise ValueError(f"Workspace '{name}' already exists")
        ws = Workspace(name, source_plugin, graph)
        self.workspaces[name] = ws
        if self.active_workspace_name is None:
            self.active_workspace_name = name
        return ws

    def switch_workspace(self, name: str) -> None:
        if name not in self.workspaces:
            raise ValueError(f"Workspace '{name}' does not exist")
        self.active_workspace_name = name

    def delete_workspace(self, name: str) -> None:
        if name not in self.workspaces:
            raise ValueError(f"Workspace '{name}' does not exist")
        del self.workspaces[name]
        if self.active_workspace_name == name:
            self.active_workspace_name = next(iter(self.workspaces), None)

    def reset_workspace(self, name: str) -> None:
        if name not in self.workspaces:
            raise ValueError(f"Workspace '{name}' does not exist")
        self.workspaces[name].reset_active_graph()

    def get_active_workspace(self) -> Optional[Workspace]:
        if self.active_workspace_name is None:
            return None
        return self.workspaces[self.active_workspace_name]

    def get_active_graph(self) -> Optional[Graph]:
        ws = self.get_active_workspace()
        if ws is None:
            return None
        return ws.get_active_graph()

    def list_workspaces(self) -> Dict[str, Workspace]:
        return self.workspaces

    def create_workspace_from_plugin(self, plugin: DataSourcePlugin, name: str, **kwargs) -> Workspace:
        """
        Kreira workspace automatski koristeci DataSourcePlugin.
        kwargs se prosledjuju plugin-u (npr. path, url)
        """
        graph: Graph = plugin.load(**kwargs)
        return self.create_workspace(name, plugin, graph)

    def __str__(self):
        active = self.active_workspace_name or "None"
        return f"WorkspaceManager(active='{active}', total={len(self.workspaces)})"