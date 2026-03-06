from abc import ABC, abstractmethod
from typing import Any, Optional
from graph.api.model.graph import Graph
from graph.api.events import EventType


class Plugin(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def identifier(self) -> str:
        pass


class DataSourcePlugin(Plugin):
    @abstractmethod
    def load(self, **kwargs) -> Graph:
        """
        Plugin ucitava neki izvor podataka i vraca Graph (domain model).
        kwargs: npr. path, url, credentials, config...
        """
        pass


class VisualizerPlugin(Plugin):
    @abstractmethod
    def visualize(self, graph: Graph, **kwargs) -> Any:
        """
        Plugin dobija Graph i vraca rezultat vizualizacije.
        Any: npr. HTML/SVG string, bytes (slika), putanja do fajla, itd.
        """
        pass
    
    def supported_events(self) -> list[EventType]:
        """
        Return list of event types this visualizer can emit.
        
        Default implementation returns empty list (no events).
        Override this method if your visualizer emits events for
        cross-view synchronization or user interaction.
        
        Returns:
            List of EventType that this visualizer supports
        """
        return []
    
    def embedding_mode(self) -> str:
        """
        Return the preferred embedding mode for this visualizer.
        
        Possible values:
            - "iframe": Content should be loaded in an iframe (default for HTML)
            - "inline": Content can be inserted directly into the page
            - "image": Content is a static image
            - "external": Content should be opened externally
        
        Returns:
            String indicating embedding mode
        """
        return "iframe"
    
    def get_event_script(self) -> Optional[str]:
        """
        Return JavaScript code snippet for event communication protocol.
        
        This method provides the standard event emission code that the
        visualizer can include in its output. This decouples the specific
        communication mechanism (postMessage, WebSocket, etc.) from the plugin.
        
        Returns:
            JavaScript code as string, or None if no events supported
        """
        if not self.supported_events():
            return None
        
        # Standard postMessage-based event protocol
        return """
        // Standard event emission helper
        window.emitVisualizerEvent = function(type, data) {
            if (window.parent !== window) {
                window.parent.postMessage({ type: type, data: data }, '*');
            }
        };
        """