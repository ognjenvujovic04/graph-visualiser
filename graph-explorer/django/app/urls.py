from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("graph-data/", views.graph_data, name="graph_data"),
    path('api/load/',   views.load_file,    name='load_file'),
    path('api/search/', views.apply_search, name='apply_search'),
    path('api/filter/', views.apply_filter, name='apply_filter'),
    path('api/reset/',  views.reset_graph,  name='reset_graph'),
    path('api/visualize/', views.visualize_graph, name='visualize_graph'),
]