from nautobot.apps.api import NautobotModelViewSet

from ..models import ProtocolType, Route, RoutingProtocol, RoutingTable
from .serializers import ProtocolTypeSerializer, RouteSerializer, RoutingProtocolSerializer, RoutingTableSerializer


class ProtocolTypeViewSet(NautobotModelViewSet):
    queryset = ProtocolType.objects.all()
    serializer_class = ProtocolTypeSerializer


class RoutingTableViewSet(NautobotModelViewSet):
    queryset = RoutingTable.objects.all()
    serializer_class = RoutingTableSerializer


class RoutingProtocolViewSet(NautobotModelViewSet):
    queryset = RoutingProtocol.objects.all()
    serializer_class = RoutingProtocolSerializer


class RouteViewSet(NautobotModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
