"""
Flask Graph Explorer Application
Main application file for the Flask version of Graph Explorer
"""
import json
import os
import uuid
from flask import Flask, render_template, request, jsonify
from pathlib import Path

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

# Global state
workspaces = {}
current_workspace_id = None
plugin_registry = None
datasource_factory = None
visualizer_factory = None


class Workspace:
    """
    Represents a workspace containing:
    - Original graph from data source
    - Current graph (after filters/search)
    - Filter and search history
    """
    def __init__(self, workspace_id: str, name: str, graph, datasource_name: str, datasource_params: dict):
        self.id = workspace_id
        self.name = name
        self.original_graph = graph
        self.current_graph = graph
        self.datasource_name = datasource_name
        self.datasource_params = datasource_params
        self.history = []

    def apply_operation(self, operation_type: str, params: dict, result_graph):
        """Record an operation and update current graph."""
        self.history.append({
            'type': operation_type,
            'params': params
        })
        self.current_graph = result_graph

    def reset(self):
        """Reset to original graph."""
        self.current_graph = self.original_graph
        self.history = []


def initialize_plugins():
    """Initialize plugins from platform."""
    global plugin_registry, datasource_factory, visualizer_factory
    
    try:
        from graph.use_cases.plugin_recognition import PluginRegistry
        from graph.factory.data_source_factory import DataSourceFactory
        from graph.factory.visualizer_factory import VisualizerFactory
        
        plugin_registry = PluginRegistry()
        
        try:
            plugin_registry.load_all()
            print("✓ All plugins loaded successfully")
        except ModuleNotFoundError as e:
            print(f"⚠️  Warning: Could not load plugin: {e}")
            print("   Continuing with available plugins...")
            load_plugins_individually()
        except Exception as e:
            print(f"⚠️  Warning: Error loading plugins: {e}")
            load_plugins_individually()
        
        datasource_factory = DataSourceFactory(plugin_registry)
        visualizer_factory = VisualizerFactory(plugin_registry)
        
    except Exception as e:
        print(f"Error initializing plugins: {e}")


def load_plugins_individually():
    """Load plugins one by one, skipping broken ones."""
    from importlib.metadata import entry_points
    from graph.use_cases.consts import DATASOURCE_GROUP, VISUALIZER_GROUP
    
    print("Loading datasources...")
    plugin_registry._PluginRegistry__datasources = []
    try:
        for ep in entry_points(group=DATASOURCE_GROUP):
            try:
                cls = ep.load()
                plugin = cls()
                plugin_registry._PluginRegistry__datasources.append(plugin)
                print(f"  ✓ Loaded: {ep.name}")
            except Exception as e:
                print(f"  ✗ Failed to load {ep.name}: {e}")
    except Exception as e:
        print(f"  ✗ Error loading datasources: {e}")
    
    print("Loading visualizers...")
    plugin_registry._PluginRegistry__visualizers = []
    try:
        for ep in entry_points(group=VISUALIZER_GROUP):
            try:
                cls = ep.load()
                plugin = cls()
                plugin_registry._PluginRegistry__visualizers.append(plugin)
                print(f"  ✓ Loaded: {ep.name}")
            except Exception as e:
                print(f"  ✗ Failed to load {ep.name}: {e}")
    except Exception as e:
        print(f"  ✗ Error loading visualizers: {e}")


def create_sample_data():
    """Create a sample JSON file if it doesn't exist."""
    sample_data = {
        "@id": "root",
        "name": "Root",
        "children": [
            {
                "@id": "n1",
                "name": "Level1-1",
                "children": [
                    {
                        "@id": "n1_1",
                        "name": "Level2-1",
                        "children": [
                            {"@id": "n1_1_1", "name": "Leaf 1"},
                            {"@id": "n1_1_2", "name": "Leaf 2"}
                        ]
                    },
                    {
                        "@id": "n1_2",
                        "name": "Level2-2",
                        "children": [
                            {"@id": "n1_2_1", "name": "Leaf 3"},
                            {"@id": "n1_2_2", "name": "Leaf 4"}
                        ]
                    }
                ]
            },
            {
                "@id": "n2",
                "name": "Level1-2",
                "children": [
                    {
                        "@id": "n2_1",
                        "name": "Level2-3",
                        "children": [
                            {"@id": "n2_1_1", "name": "Leaf 5"},
                            {"@id": "n2_1_2", "name": "Leaf 6"}
                        ]
                    }
                ]
            }
        ]
    }
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    sample_path = os.path.join(project_root, 'sample_demo.json')
    with open(sample_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)
    
    return sample_path


# Routes

@app.route('/', methods=['GET'])
def index():
    """Main page of the application."""
    datasources = []
    visualizers = []
    
    if plugin_registry:
        try:
            datasources = [
                {'name': ds.name(), 'identifier': ds.identifier()} 
                for ds in plugin_registry.datasources
            ]
        except Exception as e:
            print(f"Warning: Error loading datasources: {e}")
        
        try:
            visualizers = [
                {'name': viz.name(), 'identifier': viz.identifier()} 
                for viz in plugin_registry.visualizers
            ]
        except Exception as e:
            print(f"Warning: Error loading visualizers: {e}")
    
    context = {
        'datasources': datasources,
        'visualizers': visualizers,
        'workspaces': list(workspaces.values()),
        'current_workspace_id': current_workspace_id,
        'has_demo': 'demo-workspace' in workspaces,
    }
    
    return render_template('index.html', **context)


@app.route('/demo/', methods=['GET'])
def create_demo_workspace():
    """Create a demo workspace with sample data from demo.json or sample.json."""
    global current_workspace_id
    
    try:
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        print("\n" + "="*60)
        print("DEMO ENDPOINT CALLED")
        print("="*60)
        print(f"Project root: {project_root}")
        
        # Try demo.json first, then sample.json
        demo_path = os.path.join(project_root, 'demo.json')
        sample_path = os.path.join(project_root, 'data/sample.json')
        
        print(f"Looking for demo.json: {demo_path} - exists: {os.path.exists(demo_path)}")
        print(f"Looking for data/sample.json: {sample_path} - exists: {os.path.exists(sample_path)}")
        
        if os.path.exists(demo_path):
            json_file = demo_path
            print(f"✓ Using demo.json")
        elif os.path.exists(sample_path):
            json_file = sample_path
            print(f"✓ Using data/sample.json")
        else:
            print(f"✗ No JSON files found, creating sample data")
            json_file = create_sample_data()
            print(f"✓ Created sample data at: {json_file}")
        
        print(f"Loading from: {json_file}")
        
        # Verify file exists and is readable
        with open(json_file, 'r', encoding='utf-8') as f:
            test_read = f.read(100)
            print(f"✓ File is readable, first 100 chars: {test_read[:50]}...")
        
        # Load graph from JSON datasource plugin
        print(f"Creating JSON datasource plugin...")
        
        if not datasource_factory:
            raise RuntimeError("datasource_factory not initialized")
        
        print(f"datasource_factory exists: {datasource_factory}")
        
        datasource_plugin = datasource_factory.create_plugin('json')
        print(f"✓ JSON plugin created")
        
        print(f"Calling load() with path={json_file}")
        graph = datasource_plugin.load(path=json_file)
        
        print(f"✓ Graph loaded successfully")
        print(f"  - Nodes: {len(graph.nodes)}")
        print(f"  - Edges: {len(graph.edges)}")
        
        # Create workspace
        workspace_id = 'demo-workspace'
        workspace = Workspace(
            workspace_id=workspace_id,
            name='Demo: Sample Graph',
            graph=graph,
            datasource_name='JSON File',
            datasource_params={'path': json_file}
        )
        
        workspaces[workspace_id] = workspace
        current_workspace_id = workspace_id
        
        print(f"✓ Workspace '{workspace_id}' created and set as current")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'workspace_id': workspace_id,
            'message': f'Demo workspace created with {len(graph.nodes)} nodes and {len(graph.edges)} edges'
        })
        
    except Exception as e:
        import traceback
        error_str = str(e)
        traceback_str = traceback.format_exc()
        print(f"\n✗ ERROR in demo endpoint:")
        print(error_str)
        print(f"\nFull traceback:")
        print(traceback_str)
        print("="*60 + "\n")
        
        return jsonify({
            'success': False,
            'error': error_str
        }), 500


@app.route('/workspaces/', methods=['GET'])
def list_workspaces():
    """List all workspaces as JSON."""
    workspaces_data = [
        {
            'id': ws.id,
            'name': ws.name,
            'datasource': ws.datasource_name,
            'node_count': len(ws.current_graph.nodes),
            'edge_count': len(ws.current_graph.edges),
            'operations': len(ws.history),
        }
        for ws in workspaces.values()
    ]
    
    return jsonify({
        'workspaces': workspaces_data,
        'current_workspace_id': current_workspace_id
    })


@app.route('/workspace/create/', methods=['POST'])
def create_workspace():
    """Create a new workspace by loading data from a datasource plugin."""
    global current_workspace_id
    
    try:
        data = request.get_json()
        datasource_id = data.get('datasource')
        workspace_name = data.get('name', f'Workspace {len(workspaces) + 1}')
        params = data.get('params', {})
        
        if not datasource_id:
            return jsonify({'error': 'Missing datasource parameter'}), 400
        
        if not datasource_factory:
            return jsonify({'error': 'Plugin system not initialized'}), 500
        
        # Load graph from datasource plugin
        datasource_plugin = datasource_factory.create_plugin(datasource_id)
        graph = datasource_plugin.load(**params)
        
        # Create workspace
        workspace_id = str(uuid.uuid4())
        workspace = Workspace(
            workspace_id=workspace_id,
            name=workspace_name,
            graph=graph,
            datasource_name=datasource_plugin.name(),
            datasource_params=params
        )
        
        workspaces[workspace_id] = workspace
        current_workspace_id = workspace_id
        
        return jsonify({
            'success': True,
            'workspace_id': workspace_id,
            'message': f'Workspace created with {len(graph.nodes)} nodes and {len(graph.edges)} edges'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/workspace/<workspace_id>/select/', methods=['POST'])
def select_workspace(workspace_id):
    """Switch to a different workspace."""
    global current_workspace_id
    
    if workspace_id not in workspaces:
        return jsonify({'error': 'Workspace not found'}), 404
    
    current_workspace_id = workspace_id
    return jsonify({'success': True, 'workspace_id': workspace_id})


@app.route('/workspace/<workspace_id>/delete/', methods=['POST'])
def delete_workspace(workspace_id):
    """Delete a workspace."""
    global current_workspace_id
    
    if workspace_id not in workspaces:
        return jsonify({'error': 'Workspace not found'}), 404
    
    del workspaces[workspace_id]
    
    # If this was the current workspace, switch to another or None
    if current_workspace_id == workspace_id:
        if workspaces:
            current_workspace_id = list(workspaces.keys())[0]
        else:
            current_workspace_id = None
    
    return jsonify({'success': True})


@app.route('/workspace/<workspace_id>/reset/', methods=['POST'])
def reset_workspace(workspace_id):
    """Reset workspace to original graph (remove all filters/searches)."""
    if workspace_id not in workspaces:
        return jsonify({'error': 'Workspace not found'}), 404
    
    workspace = workspaces[workspace_id]
    workspace.reset()
    
    return jsonify({'success': True, 'message': 'Workspace reset to original graph'})


@app.route('/graph/visualize/', methods=['GET'])
def visualize_graph():
    """Visualize the current workspace's graph using a visualizer plugin."""
    if not current_workspace_id:
        return jsonify({'error': 'No active workspace'}), 400
    
    workspace = workspaces.get(current_workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404
    
    visualizer_id = request.args.get('visualizer', 'simple')
    
    try:
        visualizer = visualizer_factory.create_plugin(visualizer_id)
        html_output = visualizer.visualize(workspace.current_graph)
        return html_output, 200, {'Content-Type': 'text/html'}
        
    except ValueError as e:
        # Visualizer plugin not found, try default
        if visualizer_id != 'simple':
            try:
                visualizer = visualizer_factory.create_plugin('simple')
                html_output = visualizer.visualize(workspace.current_graph)
                return html_output, 200, {'Content-Type': 'text/html'}
            except Exception as fallback_error:
                return jsonify({'error': f'No visualizers available: {fallback_error}'}), 500
        return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        return jsonify({'error': f'Visualization error: {str(e)}'}), 500


@app.route('/graph/search/', methods=['POST'])
def search_graph():
    """Search the graph and create a subgraph."""
    try:
        if not current_workspace_id:
            return jsonify({'error': 'No active workspace'}), 400
        
        workspace = workspaces.get(current_workspace_id)
        if not workspace:
            return jsonify({'error': 'Workspace not found'}), 404
        
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Missing query parameter'}), 400
        
        # Apply search operation on current graph
        from graph.api.model.search import SearchOperation
        search_op = SearchOperation(query)
        result_graph = search_op.execute(workspace.current_graph)
        
        # Update workspace
        workspace.apply_operation('search', {'query': query}, result_graph)
        
        return jsonify({
            'success': True,
            'node_count': len(result_graph.nodes),
            'edge_count': len(result_graph.edges),
            'message': f'Search returned {len(result_graph.nodes)} nodes'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/graph/filter/', methods=['POST'])
def filter_graph():
    """Filter the graph based on attribute conditions."""
    try:
        if not current_workspace_id:
            return jsonify({'error': 'No active workspace'}), 400
        
        workspace = workspaces.get(current_workspace_id)
        if not workspace:
            return jsonify({'error': 'Workspace not found'}), 404
        
        data = request.get_json()
        filter_expr = data.get('expression', '')
        
        if not filter_expr:
            return jsonify({'error': 'Missing expression parameter'}), 400
        
        # Apply filter operation on current graph
        from graph.api.model.filter import FilterOperation
        filter_op = FilterOperation(filter_expr)
        result_graph = filter_op.execute(workspace.current_graph)
        
        # Update workspace
        workspace.apply_operation('filter', {'expression': filter_expr}, result_graph)
        
        return jsonify({
            'success': True,
            'node_count': len(result_graph.nodes),
            'edge_count': len(result_graph.edges),
            'message': f'Filter returned {len(result_graph.nodes)} nodes'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/graph/data/', methods=['GET'])
def get_graph_data():
    """Get the current graph data as JSON for client-side visualization."""
    if not current_workspace_id:
        return jsonify({'error': 'No active workspace'}), 400
    
    workspace = workspaces.get(current_workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404
    
    graph = workspace.current_graph
    
    # Convert graph to JSON-serializable format
    nodes_data = []
    for node in graph.nodes:
        node_dict = {
            'id': node.id,
            'attributes': {}
        }
        for key, attr_value in node.attributes.items():
            node_dict['attributes'][key] = attr_value.value
        nodes_data.append(node_dict)
    
    edges_data = []
    for edge in graph.edges:
        edge_dict = {
            'id': edge.id,
            'source': edge.source.id,
            'target': edge.target.id,
            'attributes': {}
        }
        for key, attr_value in edge.attributes.items():
            edge_dict['attributes'][key] = attr_value.value
        edges_data.append(edge_dict)
    
    return jsonify({
        'nodes': nodes_data,
        'edges': edges_data,
        'directed': graph.directed,
        'cyclic': graph.cyclic
    })


@app.route('/datasources/', methods=['GET'])
def list_datasources():
    """List all available datasource plugins."""
    try:
        datasources = [
            {
                'name': ds.name(),
                'identifier': ds.identifier()
            }
            for ds in plugin_registry.datasources
        ]
    except Exception as e:
        datasources = []
        print(f"Error loading datasources: {e}")
    
    return jsonify({'datasources': datasources})


@app.route('/visualizers/', methods=['GET'])
def list_visualizers():
    """List all available visualizer plugins."""
    try:
        visualizers = [
            {
                'name': viz.name(),
                'identifier': viz.identifier()
            }
            for viz in plugin_registry.visualizers
        ]
    except Exception as e:
        visualizers = []
        print(f"Error loading visualizers: {e}")
    
    return jsonify({'visualizers': visualizers})


if __name__ == '__main__':
    # Initialize plugins before running
    initialize_plugins()
    
    # Run Flask app
    app.run(debug=True, host='127.0.0.1', port=5000)
