from abc import ABC, abstractmethod

from graph.api.services import Plugin

class PluginFactory(ABC):
    @abstractmethod
    def create_plugin(self)->Plugin:
        pass