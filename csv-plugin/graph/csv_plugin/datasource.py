
from graph.api.model import Graph
from graph.api.services.plugin import DataSourcePlugin
from .parser import CsvGraphParser

class CSVDataSource(DataSourcePlugin):
    def __init__(self):
        self.__parser=CsvGraphParser()

    def name(self)->str:
        return "CSV datasource"
    def identifier(self) -> str:
        return "csv"
    def load(self, **kwargs) -> Graph:
        path= kwargs['path']
        if not path:
            raise ValueError("Missing path")
        directed = kwargs.get("directed", "y").lower() == "y"

        return self.__parser.parse(path, directed=directed)
