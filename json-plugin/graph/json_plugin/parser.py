from datetime import datetime
from typing import Any, Dict, Optional

from graph.api.model.graph import Graph
from graph.api.model.node import Node
from graph.api.model.attributes import AttributeType, AttributeValue

from .config import JsonConfig


class JsonGraphParser(object):

    def parse(self, data: Any, cfg: JsonConfig, dir:str) -> Graph:
        # JSON moze biti ciklican, default dozvoli cikluse
        graph = Graph(directed=True, cyclic=True)
        if dir=="y":
            graph.directed=True
        else:
            graph.directed=False
        # PASS 1: index svih @id (da prepoznamo string reference)
        id_index: Dict[str, str] = {}
        self.__index_ids(data, cfg, id_index)

        # PASS 2: izgradi graf
        self.__build(data, cfg, graph, id_index, parent_node=None, edge_label=None)
        if not graph.has_cycle():
            graph.cyclic = False
        return graph

    # ---------- PASS 1: index all @id ----------

    def __index_ids(self, obj: Any, cfg: JsonConfig, id_index: Dict[str, str]) -> None:
        if isinstance(obj, dict):
            if cfg.id_key in obj and isinstance(obj[cfg.id_key], str):
                _id = obj[cfg.id_key]
                id_index[_id] = _id
            for v in obj.values():
                self.__index_ids(v, cfg, id_index)

        elif isinstance(obj, list):
            for item in obj:
                self.__index_ids(item, cfg, id_index)

    # ---------- PASS 2: build graph ----------

    def __build(
        self,
        obj: Any,
        cfg: JsonConfig,
        graph: Graph,
        id_index: Dict[str, str],
        parent_node: Optional[Node],
        edge_label: Optional[str],
    ) -> Optional[Node]:

        # ---------------- DICT -> Node ----------------
        if isinstance(obj, dict):
            node_id = self.__resolve_node_id(obj, cfg)

            # get/create node
            node = graph.get_node(node_id)
            if node is None:
                node = Node(node_id)
                graph.add_node(node)

            # link parent -> this node (ako postoji roditelj)
            if parent_node is not None and edge_label is not None:
                graph.add_edge(parent_node, node, edge_label)

            # obradi polja
            for k, v in obj.items():
                if k == cfg.id_key:
                    continue

                # eksplicitna referenca: {"@ref": "X"}
                if isinstance(v, dict) and cfg.ref_key in v and isinstance(v[cfg.ref_key], str):
                    ref_id = v[cfg.ref_key]
                    target_id = id_index.get(ref_id, ref_id)

                    target_node = graph.get_node(target_id)
                    if target_node is None:
                        target_node = Node(target_id)
                        graph.add_node(target_node)

                    graph.add_edge(node, target_node, k)
                    continue

                # string referenca: "X" gde X postoji kao @id
                if cfg.treat_string_refs_as_ids and isinstance(v, str) and v in id_index:
                    target_id = id_index[v]

                    target_node = graph.get_node(target_id)
                    if target_node is None:
                        target_node = Node(target_id)
                        graph.add_node(target_node)

                    graph.add_edge(node, target_node, k)
                    continue

                # child strukture
                if isinstance(v, (dict, list)):
                    self.__build(v, cfg, graph, id_index, parent_node=node, edge_label=k)
                else:
                    # primitive -> atribut
                    node.add_attribute(k, self.__to_attr_value(v))

            return node

        # ---------------- LIST -> multiple children ----------------
        if isinstance(obj, list):
            # listu tretiramo kao vise children pod istim labelom (edge_label)
            for item in obj:
                if isinstance(item, (dict, list)):
                    self.__build(item, cfg, graph, id_index, parent_node=parent_node, edge_label=edge_label)
                else:
                    # primitive u listi: za sada preskoci (mozes kasnije kao list-atribut)
                    pass
            return None

        return None


    def __resolve_node_id(self, obj: Dict[str, Any], cfg: JsonConfig) -> str:
        if cfg.id_key in obj and isinstance(obj[cfg.id_key], str):
            return obj[cfg.id_key]
        # fallback anon id (prva verzija)
        return f"anon_{id(obj)}"

    def __to_attr_value(self, v: Any) -> AttributeValue:
        # bool/null -> string
        if v is None or isinstance(v, bool):
            return AttributeValue(AttributeType.STR, str(v))

        if isinstance(v, int):
            return AttributeValue(AttributeType.INT, v)

        if isinstance(v, float):
            return AttributeValue(AttributeType.FLOAT, v)

        if isinstance(v, str):
            s = v.strip()

            # date: YYYY-MM-DD
            if len(s) == 10 and s[4] == "-" and s[7] == "-":
                try:
                    d = datetime.strptime(s, "%Y-%m-%d")
                    return AttributeValue(AttributeType.DATE, d)
                except ValueError:
                    pass

            # int/float string
            try:
                if "." in s:
                    return AttributeValue(AttributeType.FLOAT, float(s))
                return AttributeValue(AttributeType.INT, int(s))
            except ValueError:
                return AttributeValue(AttributeType.STR, v)

        return AttributeValue(AttributeType.STR, str(v))