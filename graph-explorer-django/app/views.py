import json
import os
import tempfile
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

try:
    from graph.facade.facade import PlatformFacade
    _facade_available = True
except ImportError:
    PlatformFacade = None
    _facade_available = False


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"

DEFAULT_PATHS = {
    "json": DATA_DIR / "sample.json",
    "csv": DATA_DIR / "sample.csv",
    "xml": DATA_DIR / "sample.xml",
}

DEFAULT_DATASOURCE = "json"
DEFAULT_VISUALIZER = "simple"
DEFAULT_WORKSPACE = "default"


def _get_facade() -> PlatformFacade:
    if not _facade_available:
        raise RuntimeError("PlatformFacade is not available.")
    return PlatformFacade.get_instance()


def _serialize_graph(graph) -> dict:
    if graph is None:
        return {
            "nodes": [],
            "links": [],
            "edges": [],
            "directed": False,
            "cyclic": False,
            "node_count": 0,
            "edge_count": 0,
        }

    nodes = [
        {
            "id": n.id,
            "attributes": {k: str(getattr(v, "value", v)) for k, v in n.attributes.items()}
        }
        for n in graph.nodes
    ]

    edges = [
        {
            "id": e.id,
            "source": e.source.id,
            "target": e.target.id,
            "label": getattr(e, "label", "")
        }
        for e in graph.edges
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "links": edges,
        "directed": graph.directed,
        "cyclic": graph.cyclic,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
    }


def _get_workspace_names(facade: PlatformFacade):
    try:
        workspaces = facade.list_workspaces()
        if isinstance(workspaces, dict):
            return list(workspaces.keys())
        if isinstance(workspaces, list):
            return workspaces
    except Exception:
        pass
    return []


def _get_active_workspace_name(facade: PlatformFacade) -> str:
    try:
        ws = facade.get_workspace_manager().get_active_workspace()
        if ws is None:
            return ""
        return ws.name
    except Exception:
        return ""


def _render_main_view(facade: PlatformFacade, visualizer_id: str) -> str:
    try:
        return facade.visualize(
            visualizer_id,
            width=760,
            height=520,
            theme="light",
            node_radius=18,
        )
    except Exception:
        return ""


def _build_context(
    facade: PlatformFacade,
    *,
    selected_datasource: str,
    selected_visualizer: str,
    workspace_name: str,
    selected_workspace: str,
    path: str,
    id_key: str,
    ref_key: str,
    treat_string_refs_as_ids: bool,
    directed: bool,
    main_view_html: str = "",
    error_message: str = "",
    success_message: str = "",
    search_text: str = "",
    filter_field: str = "",
    filter_operator: str = ">",
    filter_value: str = "",
    ui_status: str = "",
):
    graph = None
    try:
        graph = facade.get_active_graph()
    except Exception:
        pass

    graph_json = json.dumps(_serialize_graph(graph))

    return {
        "active_page": "home",
        "datasources": facade.get_datasource_ids() if _facade_available else [],
        "visualizers": facade.get_visualizer_ids() if _facade_available else [],
        "workspace_names": _get_workspace_names(facade) if _facade_available else [],
        "active_workspace_name": _get_active_workspace_name(facade) if _facade_available else "",
        "selected_workspace": selected_workspace,
        "selected_datasource": selected_datasource,
        "selected_visualizer": selected_visualizer,
        "workspace_name": workspace_name,
        "path": path,
        "id_key": id_key,
        "ref_key": ref_key,
        "treat_string_refs_as_ids": treat_string_refs_as_ids,
        "directed": directed,
        "main_view_html": main_view_html,
        "error_message": error_message,
        "success_message": success_message,
        "default_paths": {k: str(v) for k, v in DEFAULT_PATHS.items()},
        "graph_json": graph_json,
        "search_text": search_text,
        "filter_field": filter_field,
        "filter_operator": filter_operator,
        "filter_value": filter_value,
        "ui_status": ui_status,
    }


def _render_home_with_state(request, facade, **kwargs):
    active_ws = _get_active_workspace_name(facade)

    context = _build_context(
        facade,
        selected_datasource=DEFAULT_DATASOURCE,
        selected_visualizer=DEFAULT_VISUALIZER,
        workspace_name="",
        selected_workspace=active_ws,
        path=str(DEFAULT_PATHS.get(DEFAULT_DATASOURCE, DATA_DIR / "sample.json")),
        id_key="@id",
        ref_key="@ref",
        treat_string_refs_as_ids=True,
        directed=False,
        main_view_html=_render_main_view(facade, DEFAULT_VISUALIZER) if facade.get_active_graph() else "",
    )
    context.update(kwargs)
    return render(request, "home.html", context)


def home(request):
    if not _facade_available:
        return render(request, "home.html", {
            "active_page": "home",
            "datasources": [],
            "visualizers": [],
            "workspace_names": [],
            "active_workspace_name": "",
            "selected_workspace": "",
            "selected_datasource": DEFAULT_DATASOURCE,
            "selected_visualizer": DEFAULT_VISUALIZER,
            "workspace_name": "",
            "path": str(DEFAULT_PATHS.get(DEFAULT_DATASOURCE, DATA_DIR / "sample.json")),
            "id_key": "@id",
            "ref_key": "@ref",
            "treat_string_refs_as_ids": True,
            "directed": False,
            "main_view_html": "",
            "error_message": "PlatformFacade is not available.",
            "success_message": "",
            "default_paths": {k: str(v) for k, v in DEFAULT_PATHS.items()},
            "graph_json": json.dumps(_serialize_graph(None)),
            "search_text": "",
            "filter_field": "",
            "filter_operator": ">",
            "filter_value": "",
            "ui_status": "",
        })

    facade = _get_facade()

    selected_datasource = DEFAULT_DATASOURCE
    selected_visualizer = DEFAULT_VISUALIZER
    workspace_name = ""
    selected_workspace = ""
    path = str(DEFAULT_PATHS.get(DEFAULT_DATASOURCE, DATA_DIR / "sample.json"))
    id_key = "@id"
    ref_key = "@ref"
    treat_string_refs_as_ids = True
    directed = False

    main_view_html = ""
    error_message = ""
    success_message = ""

    if not _get_workspace_names(facade):
        try:
            facade.create_workspace(
                name=DEFAULT_WORKSPACE,
                plugin_id=DEFAULT_DATASOURCE,
                path=str(DEFAULT_PATHS[DEFAULT_DATASOURCE]),
                id_key=id_key,
                ref_key=ref_key,
                treat_string_refs_as_ids=True,
                directed=False,
            )
            try:
                facade.switch_workspace(DEFAULT_WORKSPACE)
            except Exception:
                pass
        except Exception as e:
            error_message = str(e)

    if request.method == "POST":
        action = request.POST.get("action", "").strip()

        selected_datasource = request.POST.get("plugin_id", DEFAULT_DATASOURCE).strip().lower()
        selected_visualizer = request.POST.get("visualizer_id", DEFAULT_VISUALIZER).strip().lower()
        workspace_name = request.POST.get("workspace_name", "").strip()
        selected_workspace = request.POST.get("selected_workspace", "").strip()
        path = request.POST.get("path", "").strip()
        id_key = request.POST.get("id_key", "@id").strip() or "@id"
        ref_key = request.POST.get("ref_key", "@ref").strip() or "@ref"
        treat_string_refs_as_ids = request.POST.get("treat_string_refs_as_ids") == "on"
        directed = request.POST.get("directed") == "on"

        try:
            if action == "create":
                final_workspace_name = workspace_name or DEFAULT_WORKSPACE

                facade.create_workspace(
                    name=final_workspace_name,
                    plugin_id=selected_datasource,
                    path=path,
                    id_key=id_key,
                    ref_key=ref_key,
                    treat_string_refs_as_ids=treat_string_refs_as_ids,
                    directed=directed,
                )

                # KLJUCNA IZMENA:
                facade.switch_workspace(final_workspace_name)

                success_message = f"Workspace '{final_workspace_name}' created and activated."
                selected_workspace = _get_active_workspace_name(facade)

            elif action == "switch":
                if not selected_workspace:
                    raise ValueError("Select a workspace to switch to.")
                facade.switch_workspace(selected_workspace)
                success_message = f"Switched to workspace '{selected_workspace}'."
                selected_workspace = _get_active_workspace_name(facade)

            elif action == "delete":
                if not selected_workspace:
                    raise ValueError("Select a workspace to delete.")
                facade.delete_workspace(selected_workspace)
                success_message = f"Deleted workspace '{selected_workspace}'."

                names = _get_workspace_names(facade)
                if names:
                    facade.switch_workspace(names[0])
                selected_workspace = _get_active_workspace_name(facade)

            else:
                pass

            if facade.get_active_graph() is not None:
                main_view_html = _render_main_view(facade, selected_visualizer)

        except Exception as e:
            error_message = str(e)

    else:
        try:
            if facade.get_active_graph() is not None:
                main_view_html = _render_main_view(facade, selected_visualizer)
        except Exception as e:
            error_message = str(e)

    current_active = _get_active_workspace_name(facade)
    if current_active:
        selected_workspace = current_active

    context = _build_context(
        facade,
        selected_datasource=selected_datasource,
        selected_visualizer=selected_visualizer,
        workspace_name=workspace_name,
        selected_workspace=selected_workspace,
        path=path,
        id_key=id_key,
        ref_key=ref_key,
        treat_string_refs_as_ids=treat_string_refs_as_ids,
        directed=directed,
        main_view_html=main_view_html,
        error_message=error_message,
        success_message=success_message,
    )

    return render(request, "home.html", context)


@require_GET
def graph_data(request):
    if not _facade_available:
        return JsonResponse({"error": "Platform not available"}, status=503)

    try:
        facade = _get_facade()
        graph = facade.get_active_graph()

        if graph is None:
            return JsonResponse({"error": "No active graph loaded"}, status=400)

        return JsonResponse(_serialize_graph(graph))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def load_file(request):
    if not _facade_available:
        return JsonResponse({"error": "Platform not available"}, status=503)

    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    ext = os.path.splitext(uploaded.name)[1].lower()
    plugin_map = {
        ".json": "json",
        ".csv": "csv",
        ".xml": "xml",
    }
    plugin_id = plugin_map.get(ext)

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

        facade = _get_facade()
        available = facade.get_datasource_ids()
        if plugin_id not in available:
            return JsonResponse(
                {"error": f"Plugin '{plugin_id}' not installed. Available: {available}"},
                status=400,
            )

        workspace_name = request.POST.get("workspace_name", "").strip() or DEFAULT_WORKSPACE
        visualizer_id = request.POST.get("visualizer_id", DEFAULT_VISUALIZER).strip().lower() or DEFAULT_VISUALIZER

        id_key = request.POST.get("id_key", "@id").strip() or "@id"
        ref_key = request.POST.get("ref_key", "@ref").strip() or "@ref"
        treat_string_refs_as_ids = request.POST.get("treat_string_refs_as_ids", "true").lower() in ("true", "1", "yes", "on")
        directed = request.POST.get("directed", "false").lower() in ("true", "1", "yes", "on")

        facade.create_workspace(
            name=workspace_name,
            plugin_id=plugin_id,
            path=tmp_path,
            id_key=id_key,
            ref_key=ref_key,
            treat_string_refs_as_ids=treat_string_refs_as_ids,
            directed=directed,
        )

        try:
            facade.switch_workspace(workspace_name)
        except Exception:
            pass

        graph = facade.get_active_graph()
        rendered = ""
        if graph is not None:
            rendered = _render_main_view(facade, visualizer_id)

        return JsonResponse({
            "workspace": workspace_name,
            "plugin_id": plugin_id,
            "visualizer": visualizer_id,
            "graph": _serialize_graph(graph),
            "rendered": rendered,
        })

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
def visualize_graph(request):
    if not _facade_available:
        return JsonResponse({"error": "Platform not available"}, status=503)

    try:
        body = json.loads(request.body or "{}")
        visualizer_id = body.get("visualizer", DEFAULT_VISUALIZER).strip() or DEFAULT_VISUALIZER
        width = body.get("width", 760)
        height = body.get("height", 520)

        facade = _get_facade()

        if facade.get_active_graph() is None:
            return JsonResponse({"error": "No active graph loaded"}, status=400)

        rendered = facade.visualize(
            visualizer_id,
            width=width,
            height=height,
            theme="light",
            node_radius=18,
        )

        return JsonResponse({
            "visualizer": visualizer_id,
            "rendered": rendered,
        })

    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Failed to visualize graph: {e}"}, status=500)


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
            facade = _get_facade()
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
                _get_facade(),
                search_text=search_text,
                filter_field=filter_field,
                filter_operator=filter_operator,
                filter_value=filter_value,
                ui_status=f"Error: {e}",
            )

    try:
        body = json.loads(request.body)
        query = body.get("query", "").strip()
        if not query:
            return JsonResponse({"error": "query is required"}, status=400)
        facade = _get_facade()
        facade.search(query)
        graph = facade.get_active_graph()
        return JsonResponse(_serialize_graph(graph))
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
            facade = _get_facade()
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
                _get_facade(),
                search_text=search_text,
                filter_field=field,
                filter_operator=operator,
                filter_value=value,
                ui_status=f"Error: {e}",
            )

    try:
        body = json.loads(request.body)
        field = body.get("field", "").strip()
        operator = body.get("operator", "").strip()
        value = body.get("value", "").strip()
        if not field or not operator or not value:
            return JsonResponse(
                {"error": "field, operator and value are all required"}, status=400
            )
        facade = _get_facade()
        facade.filter(f"{field} {operator} {value}")
        graph = facade.get_active_graph()
        return JsonResponse(_serialize_graph(graph))
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_POST
def reset_graph(request):
    if not _facade_available:
        return JsonResponse({"error": "Platform not available"}, status=503)

    if request.content_type and "application/json" not in request.content_type:
        try:
            facade = _get_facade()
            try:
                facade.reset_graph()
            except ValueError:
                pass
            return _render_home_with_state(
                request,
                facade,
                search_text="",
                filter_field="",
                filter_operator=">",
                filter_value="",
                ui_status="Graph reset.",
            )
        except ValueError as e:
            return _render_home_with_state(
                request,
                _get_facade(),
                ui_status=f"Error: {e}",
            )

    try:
        facade = _get_facade()
        try:
            facade.reset_graph()
        except ValueError:
            pass
        graph = facade.get_active_graph()
        return JsonResponse(_serialize_graph(graph))
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)