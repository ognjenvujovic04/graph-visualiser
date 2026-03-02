import csv

from graph.api.builder.builder import Builder
from graph.api.builder.graph_builder import GraphBuilder
from graph.api.model import Graph

class CsvGraphParser:
    def __init__(self, builder: Builder = None):
        self.__builder = builder or GraphBuilder()
    def parse(self, path: str, directed: bool) -> Graph:
        graph = self.__builder.build_graph(directed=directed, cyclic=True)
        rows = {}
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.__builder.build_node(row)
                rows[row["id"]] = row
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("parent_id"):
                    child = graph.get_node(row["id"])
                    parent = graph.get_node(row["parent_id"])
                    if parent and child:
                        self.__builder.build_edge(parent, child,"parent")
        if not graph.has_cycle():
            graph.cyclic = False

        return graph