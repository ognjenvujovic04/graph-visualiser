from abc import ABC, abstractmethod
from typing import Any
from graph.api.model.graph import Graph


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