from nautobot.apps.api import NautobotModelViewSet

from ..models import Route, RoutingProtocol, RoutingTable
from .serializers import RouteSerializer, RoutingProtocolSerializer, RoutingTableSerializer


class RoutingTableViewSet(NautobotModelViewSet):
    queryset = RoutingTable.objects.select_related("device", "vrf")
    serializer_class = RoutingTableSerializer


class RoutingProtocolViewSet(NautobotModelViewSet):
    queryset = RoutingProtocol.objects.select_related("routing_table")
    serializer_class = RoutingProtocolSerializer


class RouteViewSet(NautobotModelViewSet):
    queryset = Route.objects.select_related(
        "routing_table",
        "prefix",
        "next_hop_type",
        "source_interface",
    )
    serializer_class = RouteSerializer
