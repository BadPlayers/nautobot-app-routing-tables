from nautobot.apps.api import OrderedDefaultRouter

from .views import ProtocolTypeViewSet, RouteViewSet, RoutingProtocolViewSet, RoutingTableViewSet

router = OrderedDefaultRouter()
router.register("protocol-types", ProtocolTypeViewSet)
router.register("routing-tables", RoutingTableViewSet)
router.register("routing-protocols", RoutingProtocolViewSet)
router.register("routes", RouteViewSet)

urlpatterns = router.urls
