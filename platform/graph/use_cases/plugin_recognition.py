from importlib.metadata import entry_points
from typing import Dict, List

from graph.api.services.plugin import DataSourcePlugin, VisualizerPlugin
from .const import DATASOURCE_GROUP, VISUALIZER_GROUP


class PluginRegistry(object):
    def __init__(self):
        self.__datasources: List[DataSourcePlugin] = []
        self.__visualizers: List[VisualizerPlugin] = []

    @property
    def datasources(self):
        return self.__datasources

    @property
    def visualizers(self):
        return self.__visualizers

    def load_all(self):
        self.__datasources = self.__load_group(DATASOURCE_GROUP)
        self.__visualizers = self.__load_group(VISUALIZER_GROUP)

    def __load_group(self, group: str):
        result = []
        for ep in entry_points(group=group):
            cls = ep.load()
            plugin = cls()
            result.append(plugin)
        return result