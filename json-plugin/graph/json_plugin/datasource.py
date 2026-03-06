import json
from typing import Any

from graph.api.services.plugin import DataSourcePlugin
from graph.api.model.graph import Graph

from .parser import JsonGraphParser
from .config import JsonConfig


class JsonDataSource(DataSourcePlugin):

    def __init__(self):
        self.__parser = JsonGraphParser()

    def name(self) -> str:
        return "JSON Datasource"

    def identifier(self) -> str:
        return "json"
    
    def load(self, **kwargs) -> Graph:
        path = kwargs.get("path")
        if not path:
            raise ValueError("Missing required parameter: path")

        cfg = JsonConfig(
            id_key=kwargs.get("id_key", "@id"),
            ref_key=kwargs.get("ref_key", "@ref"),
            treat_string_refs_as_ids=bool(kwargs.get("treat_string_refs_as_ids", True)),
        )

        with open(path, "r", encoding="utf-8") as f:
            data: Any = json.load(f)

        directed = kwargs.get("directed", False)
        return self.__parser.parse(data, cfg, directed)
    
        