from nautobot.apps.api import OrderedDefaultRouter

from .views import RouteViewSet, RoutingProtocolViewSet, RoutingTableViewSet

router = OrderedDefaultRouter()
router.register("routing-tables", RoutingTableViewSet)
router.register("routing-protocols", RoutingProtocolViewSet)
router.register("routes", RouteViewSet)

urlpatterns = router.urls
