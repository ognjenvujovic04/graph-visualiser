from graph.facade.facade import PlatformFacade
from graph.cli.parser import CLIParser


def section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def run(parser: CLIParser, cmd: str):
    print(f"\n> {cmd}")
    try:
        command = parser.parse(cmd)
        result = command.execute()
        print(result)
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    facade = PlatformFacade.get_instance()
    parser = CLIParser(facade)

    # ------------------------------------------------------------------
    section("1. Available plugins")
    # ------------------------------------------------------------------
    print("Datasources:")
    for p in facade.get_datasources():
        print(f"  - {p.name()} (id='{p.identifier()}')")

    print("Visualizers:")
    for p in facade.get_visualizers():
        print(f"  - {p.name()} (id='{p.identifier()}')")

    # ------------------------------------------------------------------
    section("2. Load graph (JSON)")
    # ------------------------------------------------------------------
    graph = facade.load_graph("json", path="data/big_250.json", direct="y")
    print(f"Loaded: {graph}")

    # ------------------------------------------------------------------
    section("3. Visualize (block)")
    # ------------------------------------------------------------------
    svg = facade.visualize("block", width=900, height=700)
    with open("tests/output/facade_block.svg", "w") as f:
        f.write(svg)
    print("✓ SVG saved to tests/output/facade_block.svg")

    # ------------------------------------------------------------------
    section("4. Search via Facade")
    # ------------------------------------------------------------------
    result = facade.search("Node 1")
    print(f"Search 'Node 1': {len(result.nodes)} nodes, {len(result.edges)} edges")

    facade.reset_graph()
    print(f"Reset: {facade.get_active_graph()}")

    # ------------------------------------------------------------------
    section("5. Filter via Facade")
    # ------------------------------------------------------------------
    result = facade.filter("years > 30")
    print(f"Filter 'years > 30': {len(result.nodes)} nodes, {len(result.edges)} edges")

    facade.reset_graph()

    # ------------------------------------------------------------------
    section("6. CLI - help")
    # ------------------------------------------------------------------
    run(parser, "help")

    # ------------------------------------------------------------------
    section("7. CLI - create node")
    # ------------------------------------------------------------------
    run(parser, "create node --id=test_node --property Name=TestUser --property Age=99")

    # ------------------------------------------------------------------
    section("8. CLI - edit node")
    # ------------------------------------------------------------------
    run(parser, "edit node --id=test_node --property Age=100")

    # ------------------------------------------------------------------
    section("9. CLI - create edge")
    # ------------------------------------------------------------------
    # get first existing node id to connect to
    first_node = facade.get_active_graph().nodes[0].id
    run(parser, f"create edge --property Label=test_edge test_node {first_node}")

    # ------------------------------------------------------------------
    section("10. CLI - search")
    # ------------------------------------------------------------------
    run(parser, "search 'Node 5'")
    facade.reset_graph()

    # ------------------------------------------------------------------
    section("11. CLI - filter")
    # ------------------------------------------------------------------
    run(parser, "filter 'years > 40'")
    facade.reset_graph()

    # ------------------------------------------------------------------
    section("12. CLI - delete node (should fail - has edges)")
    # ------------------------------------------------------------------
    facade.reset_graph()
    # re-create test_node and edge since reset wiped them
    run(parser, "create node --id=test_node --property Name=TestUser")
    first_node = facade.get_active_graph().nodes[0].id
    run(parser, f"create edge --property Label=test_edge test_node {first_node}")
    run(parser, "delete node --id=test_node")

    # ------------------------------------------------------------------
    section("13. CLI - delete edge then node")
    # ------------------------------------------------------------------
    # find edge id connected to test_node
    graph = facade.get_active_graph()
    edge_to_delete = None
    for e in graph.edges:
        if e.source.id == "test_node" or e.target.id == "test_node":
            edge_to_delete = e.id
            break

    if edge_to_delete:
        run(parser, f"delete edge --id={edge_to_delete}")
        run(parser, "delete node --id=test_node")
    else:
        print("No edge found for test_node")

    # ------------------------------------------------------------------
    section("14. CLI - reset")
    # ------------------------------------------------------------------
    run(parser, "reset")

    # ------------------------------------------------------------------
    section("15. CLI - clear")
    # ------------------------------------------------------------------
    run(parser, "clear")
    g = facade.get_active_graph()
    print(f"After clear: {g}")

    # ------------------------------------------------------------------
    section("16. CLI - unknown command")
    # ------------------------------------------------------------------
    run(parser, "explode everything")

    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()