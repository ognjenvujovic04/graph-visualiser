from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("graph-data/", views.graph_data, name="graph_data"),
]