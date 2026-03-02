from graph.json_plugin.datasource import JsonDataSource
from graph.csv_plugin.datasource import CSVDataSource;

from graph.use_cases.plugin_recognition import PluginRegistry
from graph.factory.data_source_factory import DataSourceFactory
from graph.factory.visualizer_factory import VisualizerFactory


#Testiranje da li funkcionalnost radi, ovo vrv nece postojati kasnije

def main():

    directed=input("Directed y/n: ")
    data=input("Data source: 1. JSON or 2. CSV: ")
    registry = PluginRegistry()
    registry.load_all()
    ds_factory = DataSourceFactory(registry)
    if data == "1":
        ds = ds_factory.create_plugin("json")
        #g = ds.load(path="sample.json", direct=directed)  # --> aciklican, neusmeren
        g = ds.load(path="big_250.json",direct=directed) #--> primer ciklicnog i umerenog
    else:
        ds = ds_factory.create_plugin("csv")
       # g = ds.load(path="sample.csv", direct=directed)
        g = ds.load(path="big_250.csv", direct=directed)

    print("\nNODES:")
    for n in g.nodes:
        print(" -", n.id)
        for k, v in n.attributes.items():
            print(f"    {k} = {v.value} ({v.type})")

    print("\nEDGES:")
    for e in g.edges:
        print(f" - {e.id}: {e.source.id} -> {e.target.id}  label='{e.label}'")

    # BFS od prvog noda (ili od A ako postoji)
    start = g.get_node("A")
    if start is None and len(g.nodes) > 0:
        start = g.nodes[0]

    if start is not None:
        g.print_bfs(start)

    print("\n=============Graph properties============")
    print(g)
    print("=========================================")


if __name__ == "__main__":
    main()