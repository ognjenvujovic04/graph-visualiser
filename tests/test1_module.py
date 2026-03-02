from graph.json_plugin.datasource import JsonDataSource


#Testiranje da li funkcionalnost radi, ovo vrv nece postojati kasnije

def main():

    directed=input("Directed y/n: ")
    ds = JsonDataSource()
    g = ds.load(path="sample.json",direct=directed) #--> aciklican, neusmeren
    #g = ds.load(path="big_250.json",direct=directed) #--> primer ciklicnog i umerenog
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