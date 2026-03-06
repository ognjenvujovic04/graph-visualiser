import json
import random
import sys


def build_chain(n: int, add_cycles: bool = True, cycle_every: int = 25):
    """
    Pravi "lanac" od n cvorova:
    node0 -> children[0] -> children[0] -> ...
    Svaki node ima @id, name, index, years.
    Opciono dodaje cikluse: povremeno ubaci ref na neki prethodni id.
    """
    ids = [f"n{i}" for i in range(n)]

    # root
    root = {
        "@id": ids[0],
        "name": "Node 0",
        "index": 0,
        "years": 20,
        "children": []
    }

    current = root
    for i in range(1, n):
        node = {
            "@id": ids[i],
            "name": f"Node {i}",
            "index": i,
            "years": 20 + (i % 50),
            "children": []
        }

        # osnovna veza: current --children--> node
        current["children"].append(node)

        # ciklus: node ima "parent" koji pokazuje na neki raniji @id (string ref)
        if add_cycles and (i % cycle_every == 0):
            # izaberi random prethodni id (ukljucujuci root)
            target = random.choice(ids[:i])
            node["parent"] = target  # string ref, kao u specifikaciji

        # pomeri se dalje u lanac
        current = node

    return root


def main():
    # defaulti
    out_path = "data/big_250.json"
    n = 250
    add_cycles = True

    # opcioni arg: putanja fajla
    if len(sys.argv) >= 2:
        out_path = sys.argv[1]

    # opcioni arg: broj cvorova
    if len(sys.argv) >= 3:
        n = int(sys.argv[2])

    # opcioni arg: cycles on/off (true/false)
    if len(sys.argv) >= 4:
        add_cycles = sys.argv[3].lower() in ("1", "true", "yes", "y")

    data = build_chain(n=n, add_cycles=add_cycles, cycle_every=25)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Generated {n} nodes -> {out_path} (cycles={'ON' if add_cycles else 'OFF'})")


if __name__ == "__main__":
    main()