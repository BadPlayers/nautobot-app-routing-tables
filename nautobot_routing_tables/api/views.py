"""Routing UI views and the table-to-routes creation workflow."""

from nautobot.apps.api import NautobotModelViewSet

from ..filters import RouteFilterSet, RoutingProtocolFilterSet, RoutingTableFilterSet
from ..models import Route, RoutingProtocol, RoutingTable
from ..services import optimized_routes
from .serializers import RouteSerializer, RoutingProtocolSerializer, RoutingTableSerializer


class RoutingTableViewSet(NautobotModelViewSet):
    """Expose routing tables through the REST API."""

    queryset = RoutingTable.objects.select_related("device", "vrf")
    serializer_class = RoutingTableSerializer
    filterset_class = RoutingTableFilterSet


class RoutingProtocolViewSet(NautobotModelViewSet):
    """Expose per-table protocol preferences through the REST API."""

    queryset = RoutingProtocol.objects.select_related("routing_table__device", "routing_table__vrf")
    serializer_class = RoutingProtocolSerializer
    filterset_class = RoutingProtocolFilterSet


class RouteViewSet(NautobotModelViewSet):
    """Expose routes with prefetched forwarding and distance data."""

    queryset = optimized_routes(Route.objects.all())
    serializer_class = RouteSerializer
    filterset_class = RouteFilterSet
