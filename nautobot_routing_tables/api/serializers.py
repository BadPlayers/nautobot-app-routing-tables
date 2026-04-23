from rest_framework import serializers

from nautobot.apps.api import NautobotModelSerializer

from ..models import Route, RoutingProtocol, RoutingTable


class RoutingTableSerializer(NautobotModelSerializer):
    class Meta:
        model = RoutingTable
        fields = "__all__"


class RoutingProtocolSerializer(NautobotModelSerializer):
    default_admin_distance = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoutingProtocol
        fields = "__all__"


class RouteSerializer(NautobotModelSerializer):
    next_hop_display = serializers.CharField(read_only=True)
    resolved_admin_distance = serializers.IntegerField(read_only=True)

    class Meta:
        model = Route
        fields = "__all__"
