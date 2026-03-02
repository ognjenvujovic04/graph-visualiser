from graph.factory.plugin_factory import PluginFactory
from graph.api.services import Plugin
from graph.use_cases.plugin_recognition import PluginRegistry


class DataSourceFactory(PluginFactory):
    def __init__(self,registry: PluginRegistry):
        self.__registry = registry

    def create_plugin(self, name: str) -> Plugin:
        for datasource in self.__registry.datasources:
            if datasource.identifier() == name:
                return datasource
        raise ValueError(f"No datasource plugin found: {name}")
