import xml.etree.ElementTree as ET
from graph.api.builder.builder import Builder
from graph.api.builder.graph_builder import GraphBuilder
from graph.api.model import Graph
import re


class XmlGraphParser:

    def __init__(self, builder: Builder = None):
        self.__builder = builder or GraphBuilder()

    def parse(self, path: str, directed: bool) -> Graph:

        graph = self.__builder.build_graph(directed=directed, cyclic=True)

        tree = ET.parse(path)
        root = tree.getroot()

        element_to_id = {}
        tag_counter = {}

        # mapa tag -> lista elemenata (za XPath index)
        tag_elements = {}

        parent_map = {c: p for p in root.iter() for c in list(p)}

        # -------------------------
        # PASS 1 — CREATE NODES
        # -------------------------
        for parent in root.iter():

            children = list(parent)

            if children:

                node_data = {}

                node_id = parent.get("id")

                if not node_id:
                    count = tag_counter.get(parent.tag, 1)
                    node_id = f"{parent.tag}[{count}]"
                    tag_counter[parent.tag] = count + 1

                node_data["id"] = node_id

                for child in children:
                    if not list(child) and "reference" not in child.attrib:
                        text = (child.text or "").strip()
                        if text:
                            node_data[child.tag] = text

                self.__builder.build_node(node_data)

                element_to_id[parent] = node_id
                tag_elements.setdefault(parent.tag, []).append(parent)

        # -------------------------
        # PASS 2 — EDGES
        # -------------------------
        for elem in root.iter():

            if elem not in element_to_id:
                continue

            parent_node = graph.get_node(element_to_id[elem])

            # parent-child edges
            for child in list(elem):

                if child in element_to_id:
                    child_node = graph.get_node(element_to_id[child])

                    if parent_node and child_node:
                        self.__builder.build_edge(parent_node, child_node, "child")

            # XML attributes -> edges
            for attr, value in elem.attrib.items():

                if attr == "reference":
                    continue

                if value in graph.nodes:
                    target = graph.get_node(value)

                    if target:
                        self.__builder.build_edge(parent_node, target, attr)

        # -------------------------
        # PASS 3 — REFERENCE EDGES
        # -------------------------
        for elem in root.iter():

            ref = elem.attrib.get("reference")
            if not ref:
                continue

            parent_elem = parent_map.get(elem)

            if parent_elem not in element_to_id:
                continue

            source = graph.get_node(element_to_id[parent_elem])

            target = None

            # CASE 1: reference by ID
            target = graph.get_node(ref)

            # CASE 2: reference by XPath
            if not target:
                m = re.search(r'([a-zA-Z0-9_.]+)\[(\d+)\]', ref.split('/')[-1])
                if m:
                    tag = m.group(1)
                    idx = int(m.group(2)) - 1

                    if tag in tag_elements and idx < len(tag_elements[tag]):
                        target_elem = tag_elements[tag][idx]
                        target = graph.get_node(element_to_id[target_elem])

            if source and target:
                self.__builder.build_edge(source, target, "reference")

        # -------------------------
        # cycle detection
        # -------------------------
        if not graph.has_cycle():
            graph.cyclic = False

        return graph