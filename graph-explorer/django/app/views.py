import json
import os
import tempfile

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

try:
    from graph.facade.facade import PlatformFacade
    _facade_available = True
except ImportError:
    _facade_available = False

def home(request):
    graph_data = {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

    if _facade_available:
        try:
            facade = PlatformFacade.get_instance()
            graph_data = _serialize_graph(facade)
        except Exception:
            pass

    return render(request, "home.html", {
        "active_page": "home",
        "graph_json":  json.dumps(graph_data),
        "search_text": "",
        "filter_field": "",
        "filter_operator": ">",
        "filter_value": "",
        "ui_status": "",
    })


def _render_home_with_state(
    request,
    facade,
    *,
    search_text: str = "",
    filter_field: str = "",
    filter_operator: str = ">",
    filter_value: str = "",
    ui_status: str = "",
):
    graph_data = _serialize_graph(facade)
    return render(request, "home.html", {
        "active_page": "home",
        "graph_json":  json.dumps(graph_data),
        "search_text": search_text,
        "filter_field": filter_field,
        "filter_operator": filter_operator,
        "filter_value": filter_value,
        "ui_status": ui_status,
    })

@csrf_exempt
@require_POST
def load_file(request):
    if not _facade_available:
        return JsonResponse({"error": "Platform not available"}, status=503)

    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    ext = os.path.splitext(uploaded.name)[1].lower()
    plugin_map = {".json": "json", ".csv": "csv", ".xml": "xml"}
    plugin_id  = plugin_map.get(ext)
    if not plugin_id:
        return JsonResponse(
            {"error": f"Unsupported file type '{ext}'. Supported: .json, .csv, .xml"},
            status=400,
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        facade    = PlatformFacade.get_instance()
        available = facade.get_datasource_ids()

        if plugin_id not in available:
            return JsonResponse(
                {"error": f"Plugin '{plugin_id}' not installed. Available: {available}"},
                status=400,
            )

        facade.load_graph(plugin_id, workspace_name="default", path=tmp_path)
        return JsonResponse(_serialize_graph(facade))

    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Failed to load file: {e}"}, status=500)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

@csrf_exempt
@require_POST
def apply_search(request):
    if not _facade_available:
        return JsonResponse({"error": "Platform not available"}, status=503)

    if request.content_type and "application/json" not in request.content_type:
        search_text = request.POST.get("search_text", "").strip()
        filter_field = ""
        filter_operator = request.POST.get("filter_operator", ">").strip() or ">"
        filter_value = ""

        try:
            facade = PlatformFacade.get_instance()
            facade.reset_graph()
            if search_text:
                facade.search(search_text)
            return _render_home_with_state(
                request,
                facade,
                search_text=search_text,
                filter_field=filter_field,
                filter_operator=filter_operator,
                filter_value=filter_value,
                ui_status="Search applied.",
            )
        except ValueError as e:
            return _render_home_with_state(
                request,
                PlatformFacade.get_instance(),
                search_text=search_text,
                filter_field=filter_field,
                filter_operator=filter_operator,
                filter_value=filter_value,
                ui_status=f"Error: {e}",
            )

    try:
        body  = json.loads(request.body)
        query = body.get("query", "").strip()
        if not query:
            return JsonResponse({"error": "query is required"}, status=400)
        facade = PlatformFacade.get_instance()
        facade.search(query)
        return JsonResponse(_serialize_graph(facade))
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_POST
def apply_filter(request):
    if not _facade_available:
        return JsonResponse({"error": "Platform not available"}, status=503)

    if request.content_type and "application/json" not in request.content_type:
        search_text = request.POST.get("search_text", "").strip()
        field = request.POST.get("filter_field", "").strip()
        operator = request.POST.get("filter_operator", ">").strip() or ">"
        value = request.POST.get("filter_value", "").strip()

        try:
            facade = PlatformFacade.get_instance()
            facade.reset_graph()
            if field and value:
                facade.filter(f"{field} {operator} {value}")
                status = "Filter applied."
            elif field or value:
                status = "Filter requires both Field and Value. Showing reset result."
            else:
                status = "Graph reset."

            return _render_home_with_state(
                request,
                facade,
                search_text=search_text,
                filter_field=field,
                filter_operator=operator,
                filter_value=value,
                ui_status=status,
            )
        except ValueError as e:
            return _render_home_with_state(
                request,
                PlatformFacade.get_instance(),
                search_text=search_text,
                filter_field=field,
                filter_operator=operator,
                filter_value=value,
                ui_status=f"Error: {e}",
            )

    try:
        body     = json.loads(request.body)
        field    = body.get("field",    "").strip()
        operator = body.get("operator", "").strip()
        value    = body.get("value",    "").strip()
        if not field or not operator or not value:
            return JsonResponse(
                {"error": "field, operator and value are all required"}, status=400)
        facade = PlatformFacade.get_instance()
        facade.filter(f"{field} {operator} {value}")
        return JsonResponse(_serialize_graph(facade))
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_POST
def reset_graph(request):
    if not _facade_available:
        return JsonResponse({"error": "Platform not available"}, status=503)

    if request.content_type and "application/json" not in request.content_type:
        try:
            facade = PlatformFacade.get_instance()
            try:
                facade.clear_graph()
            except ValueError:
                pass
            return _render_home_with_state(
                request,
                facade,
                search_text="",
                filter_field="",
                filter_operator=">",
                filter_value="",
                ui_status="Graph cleared.",
            )
        except ValueError as e:
            return _render_home_with_state(
                request,
                PlatformFacade.get_instance(),
                ui_status=f"Error: {e}",
            )

    try:
        facade = PlatformFacade.get_instance()
        try:
            facade.clear_graph()
        except ValueError:
            pass
        return JsonResponse(_serialize_graph(facade))
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_POST
def visualize_graph(request):
    if not _facade_available:
        return JsonResponse({"error": "Platform not available"}, status=503)

    try:
        body = json.loads(request.body or "{}")
        visualizer_id = body.get("visualizer", "simple").strip() or "simple"

        width = body.get("width", 1000)
        height = body.get("height", 700)

        facade = PlatformFacade.get_instance()
        rendered = facade.visualize(visualizer_id, width=width, height=height)

        return JsonResponse({
            "visualizer": visualizer_id,
            "rendered": rendered,
        })
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Failed to visualize graph: {e}"}, status=500)

def _serialize_graph(facade) -> dict:
    graph = facade.get_active_graph()
    if graph is None:
        return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

    nodes = [
        {"id": n.id,
         "attributes": {k: str(v.value) for k, v in n.attributes.items()}}
        for n in graph.nodes
    ]
    edges = [
        {"id": e.id, "source": e.source.id, "target": e.target.id, "label": e.label}
        for e in graph.edges
    ]

    return {
        "nodes":      nodes,
        "edges":      edges,
        "directed":   graph.directed,
        "cyclic":     graph.cyclic,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
    }