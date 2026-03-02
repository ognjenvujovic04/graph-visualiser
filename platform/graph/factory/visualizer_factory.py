from graph.factory.plugin_factory import PluginFactory
from graph.api.services import Plugin
from graph.use_cases.plugin_recognition import PluginRegistry

class VisualizerFactory(PluginFactory):
    def __init__(self, registry: PluginRegistry):
        self.__registry = registry

    def create_plugin(self, name: str)->Plugin:
        for plugin in self.__registry.visualizers:
            if plugin.identifier() == name:
                return plugin
        raise ValueError(f"No visualizer plugin found: {name}")