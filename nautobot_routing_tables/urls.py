"""Routing application URL registration."""

from django.urls import path
from nautobot.apps.urls import NautobotUIViewSetRouter

from . import batch, views

app_name = "nautobot_routing_tables"

router = NautobotUIViewSetRouter()
router.register("routing-tables", views.RoutingTableUIViewSet, basename="routingtable")
router.register("routing-protocols", views.RoutingProtocolUIViewSet, basename="routingprotocol")
router.register("routes", views.RouteUIViewSet, basename="route")

urlpatterns = [
    path("routing-tables/<uuid:pk>/export/", views.export_table, name="routingtable_export"),
    path("routing-tables/<uuid:pk>/add-routes/", batch.add_routes, name="routingtable_add_routes"),
    path("route-choices/", views.route_choices, name="route_choices"),
    path("config/", views.ConfigView.as_view(), name="config"),
]

urlpatterns += router.urls
