import csv
from datetime import datetime
from graph.api.model.graph import Graph
from graph.api.model.node import Node
from graph.api.model.attributes import AttributeType, AttributeValue

class CsvGraphParser:

    def parse(self, path: str, directed: bool) -> Graph:
        graph = Graph(directed=directed, cyclic=True)
        rows = {}
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                node = Node(row["id"])
                for key, value in row.items():
                    if key not in ("id", "parent_id", "ref_id"):
                        node.add_attribute(key, self.__to_attr_value(value))
                graph.add_node(node)
                rows[row["id"]] = row
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("parent_id"):
                    child = graph.get_node(row["id"])
                    parent = graph.get_node(row["parent_id"])
                    if parent and child:
                        graph.add_edge(parent, child, "parent")

        if not graph.has_cycle():
            graph.cyclic = False

        return graph

    def __to_attr_value(self, v: str) -> AttributeValue:
        if v is None or v.strip() == "":
            return AttributeValue(AttributeType.STR, "")

        s = v.strip()

        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            try:
                d = datetime.strptime(s, "%Y-%m-%d")
                return AttributeValue(AttributeType.DATE, d)
            except ValueError:
                pass

        try:
            return AttributeValue(AttributeType.INT, int(s))
        except ValueError:
            pass
        try:
            return AttributeValue(AttributeType.FLOAT, float(s))
        except ValueError:
            pass

        return AttributeValue(AttributeType.STR, v)