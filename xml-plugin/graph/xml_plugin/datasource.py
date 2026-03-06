from graph.api.model import Graph
from graph.api.services.plugin import DataSourcePlugin
from .parser import XmlGraphParser


class XMLDataSource(DataSourcePlugin):

    def __init__(self):
        self.__parser = XmlGraphParser()

    def name(self) -> str:
        return "XML/HTML datasource"

    def identifier(self) -> str:
        return "xml"

    def load(self, **kwargs) -> Graph:
        path = kwargs.get("path")

        if not path:
            raise ValueError("Missing path")

        directed = kwargs.get("directed", False)

        return self.__parser.parse(path, directed=directed)