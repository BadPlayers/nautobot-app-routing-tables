from django.urls import path
from nautobot.apps.urls import NautobotUIViewSetRouter

from . import views

app_name = "nautobot_routing_tables"

router = NautobotUIViewSetRouter()
router.register("routing-tables", views.RoutingTableUIViewSet, basename="routingtable")
router.register("routing-protocols", views.RoutingProtocolUIViewSet, basename="routingprotocol")
router.register("routes", views.RouteUIViewSet, basename="route")

urlpatterns = [
    path("config/", views.ConfigView.as_view(), name="config"),
]

urlpatterns += router.urls