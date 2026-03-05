from django.urls import include, path
from nautobot.apps.urls import NautobotUIViewSetRouter

from . import views

app_name = "nautobot_routing_tables"

router = NautobotUIViewSetRouter()
router.register("protocol-types", views.ProtocolTypeUIViewSet)
router.register("routing-tables", views.RoutingTableUIViewSet)
router.register("routing-protocols", views.RoutingProtocolUIViewSet)
router.register("routes", views.RouteUIViewSet)

urlpatterns = [
    path("config/", views.ConfigView.as_view(), name="config"),
    path("", include(router.urls)),
]
