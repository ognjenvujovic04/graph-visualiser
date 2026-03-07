from abc import ABC, abstractmethod
from typing import Any, Optional
from graph.api.model.graph import Graph
from graph.api.events import EventType


class Plugin(ABC):
    """
    Base abstract class for all platform plugins.

    Every plugin must define a human-readable name and a unique identifier.
    These methods allow the platform to register, identify, and manage plugins
    in a consistent way.
    """

    @abstractmethod
    def name(self) -> str:
        """
        Return the human-readable name of the plugin.

        Returns:
            str: Display name of the plugin.
        """
        pass

    @abstractmethod
    def identifier(self) -> str:
        """
        Return the unique identifier of the plugin.

        The identifier is used internally by the platform to distinguish
        between different plugins.

        Returns:
            str: Unique plugin identifier.
        """
        pass


class DataSourcePlugin(Plugin):
    """
    Abstract base class for data source plugins.

    Data source plugins are responsible for loading external data
    (files, APIs, databases, etc.) and converting it into the platform's
    internal Graph domain model.
    """

    @abstractmethod
    def load(self, **kwargs) -> Graph:
        """
        Load data from an external source and return a Graph.

        The plugin implementation decides how to interpret the provided
        parameters and how to construct the resulting graph.

        Examples of parameters may include:
            - file path
            - URL
            - credentials
            - configuration options

        Args:
            **kwargs: Arbitrary parameters required for loading the data source.

        Returns:
            Graph: Graph representation of the loaded data.
        """
        pass


class VisualizerPlugin(Plugin):
    """
    Abstract base class for visualization plugins.

    Visualizer plugins take a Graph as input and produce some visual
    representation of it. The result may be HTML, SVG, an image, or
    another visualization format supported by the platform.
    """

    @abstractmethod
    def visualize(self, graph: Graph, **kwargs) -> Any:
        """
        Generate a visualization for the given graph.

        The specific format of the returned result depends on the plugin
        implementation.

        Possible outputs include:
            - HTML or SVG string
            - image bytes
            - file path
            - other visualization artifacts

        Args:
            graph (Graph): Graph to visualize.
            **kwargs: Additional visualization configuration parameters.

        Returns:
            Any: Visualization result produced by the plugin.
        """
        pass

    def supported_events(self) -> list[EventType]:
        """
        Return the list of event types that this visualizer can emit.

        Visualizers may emit events to enable cross-view synchronization
        or to react to user interactions (for example: node selection).

        The default implementation returns an empty list, meaning that
        the visualizer does not emit any events.

        Returns:
            list[EventType]: Event types supported by this visualizer.
        """
        return []

    def embedding_mode(self) -> str:
        """
        Return the preferred embedding mode for this visualizer.

        This informs the platform how the visualization output should
        be embedded into the user interface.

        Possible values:
            - "iframe": Content should be rendered inside an iframe
            - "inline": Content can be inserted directly into the page
            - "image": Content is a static image
            - "external": Content should be opened in an external viewer

        Returns:
            str: Preferred embedding mode.
        """
        return "iframe"

    def get_event_script(self) -> Optional[str]:
        """
        Return the JavaScript snippet used for emitting visualization events.

        This method provides a standard event emission helper that the
        visualizer can embed into its output. It allows communication
        between the visualization and the platform (for example through
        `postMessage`).

        If the visualizer does not support events, this method returns None.

        Returns:
            Optional[str]: JavaScript code for event emission, or None.
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