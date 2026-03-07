import os
from flask import Flask, render_template, request, jsonify
from graph.facade.facade import PlatformFacade
from graph.cli.parser import CLIParser

# Root of the project (graph-visualiser folder)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)

# Initialize facade singleton on startup
facade = PlatformFacade.get_instance()


def get_parser() -> CLIParser:
    return CLIParser(facade)


# ------------------------------------------------------------------
# Pages
# ------------------------------------------------------------------

@app.route('/')
def home():
    datasources = [{"id": p.identifier(), "name": p.name()} for p in facade.get_datasources()]
    visualizers  = [{"id": p.identifier(), "name": p.name()} for p in facade.get_visualizers()]
    return render_template('home.html', datasources=datasources, visualizers=visualizers)


# ------------------------------------------------------------------
# API endpoints
# ------------------------------------------------------------------

@app.route('/api/load', methods=['POST'])
def api_load():
    try:
        body      = request.get_json()
        plugin_id = body.get('plugin_id', 'json')
        path      = body.get('path', 'data/big_250.json')
        # resolve relative paths from project root
        if not os.path.isabs(path):
            path = os.path.join(PROJECT_ROOT, path)
        directed_str = body.get('directed', 'y')
        directed = directed_str.lower() in ('y', 'yes', 'true', '1')
        workspace_name = body.get('workspace_name')
        
        # Auto-generate workspace name if not provided
        if not workspace_name:
            # Generate name like "Workspace 1", "Workspace 2", etc.
            existing_names = list(facade.list_workspaces().keys())
            counter = 1
            while f"Workspace {counter}" in existing_names:
                counter += 1
            workspace_name = f"Workspace {counter}"
        
        graph = facade.load_graph(plugin_id, workspace_name=workspace_name, path=path, directed=directed)
        return jsonify({
            'ok': True,
            'workspace_name': workspace_name,
            'nodes': len(graph.nodes),
            'edges': len(graph.edges),
            'directed': graph.directed,
            'cyclic': graph.cyclic,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/visualize', methods=['POST'])
def api_visualize():
    try:
        body   = request.get_json()
        viz_id = body.get('visualizer_id', 'simple')
        width  = int(body.get('width', 900))
        height = int(body.get('height', 700))
        rendered_html = facade.visualize(viz_id, width=width, height=height)
        return jsonify({'ok': True, 'html': rendered_html})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/cli', methods=['POST'])
def api_cli():
    try:
        body    = request.get_json()
        raw_cmd = body.get('command', '').strip()
        if not raw_cmd:
            return jsonify({'ok': True, 'output': ''})

        parser  = get_parser()
        command = parser.parse(raw_cmd)
        output  = command.execute()

        graph = facade.get_active_graph()
        stats = {'nodes': len(graph.nodes), 'edges': len(graph.edges)} if graph else None

        return jsonify({'ok': True, 'output': output, 'stats': stats})
    except Exception as e:
        return jsonify({'ok': False, 'output': f'✗ Error: {e}', 'stats': None})


@app.route('/api/graph')
def api_graph():
    try:
        graph = facade.get_active_graph()
        if graph is None:
            return jsonify({'ok': False, 'error': 'No graph loaded'}), 400

        nodes = [{'id': n.id, 'attributes': {k: str(v.value) for k, v in n.attributes.items()}}
                 for n in graph.nodes]
        edges = [{'id': e.id, 'source': e.source.id, 'target': e.target.id, 'label': e.label}
                 for e in graph.edges]

        return jsonify({
            'ok': True,
            'nodes': nodes,
            'edges': edges,
            'directed': graph.directed,
            'cyclic': graph.cyclic,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/filter', methods=['POST'])
def api_filter():
    try:
        body = request.get_json()
        filters = body.get('filters', [])
        
        if not filters:
            return jsonify({'ok': False, 'error': 'No filters provided'}), 400
        
        graph = facade.get_active_graph()
        if graph is None:
            return jsonify({'ok': False, 'error': 'No graph loaded'}), 400
        
        # Apply filters through facade - maintains filter history in workspace
        for filter_expr in filters:
            if not filter_expr.strip():
                continue
            facade.filter(filter_expr)
        
        # Get the filtered graph
        filtered_graph = facade.get_active_graph()
        
        # Return filtered graph stats and data
        nodes = [{'id': n.id, 'attributes': {k: str(v.value) for k, v in n.attributes.items()}}
                 for n in filtered_graph.nodes]
        edges = [{'id': e.id, 'source': e.source.id, 'target': e.target.id, 'label': e.label}
                 for e in filtered_graph.edges]
        
        return jsonify({
            'ok': True,
            'nodes': nodes,
            'edges': edges,
            'nodes_count': len(filtered_graph.nodes),
            'edges_count': len(filtered_graph.edges),
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/search', methods=['POST'])
def api_search():
    try:
        body = request.get_json()
        searches = body.get('searches', [])

        if not searches:
            return jsonify({'ok': False, 'error': 'No search queries provided'}), 400

        graph = facade.get_active_graph()
        if graph is None:
            return jsonify({'ok': False, 'error': 'No graph loaded'}), 400

        # Apply searches through facade on current active graph.
        for query in searches:
            if not str(query).strip():
                continue
            facade.search(str(query).strip())

        searched_graph = facade.get_active_graph()

        nodes = [{'id': n.id, 'attributes': {k: str(v.value) for k, v in n.attributes.items()}}
                 for n in searched_graph.nodes]
        edges = [{'id': e.id, 'source': e.source.id, 'target': e.target.id, 'label': e.label}
                 for e in searched_graph.edges]

        return jsonify({
            'ok': True,
            'nodes': nodes,
            'edges': edges,
            'nodes_count': len(searched_graph.nodes),
            'edges_count': len(searched_graph.edges),
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/reset', methods=['POST'])
def api_reset():
    try:
        # Reset through facade to clear filters and search history
        facade.reset_graph()
        
        # Return original graph stats
        graph = facade.get_active_graph()
        nodes = [{'id': n.id, 'attributes': {k: str(v.value) for k, v in n.attributes.items()}}
                 for n in graph.nodes]
        edges = [{'id': e.id, 'source': e.source.id, 'target': e.target.id, 'label': e.label}
                 for e in graph.edges]
        
        return jsonify({
            'ok': True,
            'nodes': nodes,
            'edges': edges,
            'nodes_count': len(graph.nodes),
            'edges_count': len(graph.edges),
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


# ------------------------------------------------------------------
# Workspace management endpoints
# ------------------------------------------------------------------

@app.route('/api/workspaces', methods=['GET'])
def api_list_workspaces():
    """List all workspaces with their metadata."""
    try:
        workspaces = facade.list_workspaces()
        active_workspace_name = facade.get_workspace_manager().active_workspace_name
        
        ws_list = []
        for name, ws in workspaces.items():
            ws_list.append({
                'name': name,
                'plugin': ws.source_plugin.identifier(),
                'nodes': len(ws.get_active_graph().nodes),
                'edges': len(ws.get_active_graph().edges),
                'is_active': name == active_workspace_name,
                'created_at': ws.created_at.timestamp() if hasattr(ws, 'created_at') else 0
            })
        
        # Sort by creation time (oldest first)
        ws_list.sort(key=lambda w: w['created_at'])
        
        return jsonify({'ok': True, 'workspaces': ws_list})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/workspaces/switch', methods=['POST'])
def api_switch_workspace():
    """Switch to a different workspace."""
    try:
        body = request.get_json()
        name = body.get('name')
        
        if not name:
            return jsonify({'ok': False, 'error': 'Workspace name is required'}), 400
        
        facade.switch_workspace(name)
        graph = facade.get_active_graph()
        
        return jsonify({
            'ok': True,
            'nodes': len(graph.nodes),
            'edges': len(graph.edges),
            'directed': graph.directed,
            'cyclic': graph.cyclic,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/workspaces/create', methods=['POST'])
def api_create_workspace():
    """Create a new empty workspace."""
    try:
        # Auto-generate workspace name
        existing_names = list(facade.list_workspaces().keys())
        counter = 1
        while f"Workspace {counter}" in existing_names:
            counter += 1
        workspace_name = f"Workspace {counter}"
        
        # Create an empty graph
        from graph.api.model.graph import Graph
        empty_graph = Graph(directed=True, cyclic=False)
        
        # Get a dummy plugin (we'll use first available datasource plugin as placeholder)
        datasources = facade.get_datasources()
        if not datasources:
            return jsonify({'ok': False, 'error': 'No datasource plugins available'}), 400
        
        plugin = datasources[0]
        
        # Create workspace with empty graph
        manager = facade.get_workspace_manager()
        ws = manager.create_workspace(workspace_name, plugin, empty_graph)
        manager.switch_workspace(workspace_name)
        
        return jsonify({
            'ok': True,
            'workspace_name': workspace_name,
            'nodes': 0,
            'edges': 0,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/workspaces/rename', methods=['POST'])
def api_rename_workspace():
    """Rename a workspace."""
    try:
        body = request.get_json()
        old_name = body.get('old_name')
        new_name = body.get('new_name')
        
        if not old_name or not new_name:
            return jsonify({'ok': False, 'error': 'Both old_name and new_name are required'}), 400
        
        manager = facade.get_workspace_manager()
        
        if old_name not in manager.workspaces:
            return jsonify({'ok': False, 'error': f'Workspace "{old_name}" not found'}), 404
        
        if new_name in manager.workspaces:
            return jsonify({'ok': False, 'error': f'Workspace "{new_name}" already exists'}), 400
        
        # Rename by moving the workspace
        ws = manager.workspaces[old_name]
        ws.name = new_name
        manager.workspaces[new_name] = ws
        del manager.workspaces[old_name]
        
        if manager.active_workspace_name == old_name:
            manager.active_workspace_name = new_name
        
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/workspaces/delete', methods=['POST'])
def api_delete_workspace():
    """Delete a workspace."""
    try:
        body = request.get_json()
        name = body.get('name')
        
        if not name:
            return jsonify({'ok': False, 'error': 'Workspace name is required'}), 400
        
        facade.delete_workspace(name)
        
        # Get the new active workspace (if any)
        graph = facade.get_active_graph()
        if graph:
            return jsonify({
                'ok': True,
                'nodes': len(graph.nodes),
                'edges': len(graph.edges),
            })
        else:
            return jsonify({'ok': True, 'nodes': 0, 'edges': 0})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)