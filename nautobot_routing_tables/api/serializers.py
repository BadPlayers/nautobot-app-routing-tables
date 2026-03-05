from nautobot.apps.api import NautobotModelSerializer

from ..models import ProtocolType, Route, RoutingProtocol, RoutingTable


class ProtocolTypeSerializer(NautobotModelSerializer):
    class Meta:
        model = ProtocolType
        fields = "__all__"


class RoutingTableSerializer(NautobotModelSerializer):
    class Meta:
        model = RoutingTable
        fields = "__all__"


class RoutingProtocolSerializer(NautobotModelSerializer):
    class Meta:
        model = RoutingProtocol
        fields = "__all__"


class RouteSerializer(NautobotModelSerializer):
    class Meta:
        model = Route
        fields = "__all__"
