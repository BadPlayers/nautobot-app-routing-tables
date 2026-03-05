import django_filters
from nautobot.apps.filters import NautobotFilterSet

from .models import ProtocolType, Route, RoutingProtocol, RoutingTable


class RoutingTableFilterSet(NautobotFilterSet):
    class Meta:
        model = RoutingTable
        fields = ["device", "vrf", "name"]


class ProtocolTypeFilterSet(NautobotFilterSet):
    class Meta:
        model = ProtocolType
        fields = ["name", "slug"]


class RoutingProtocolFilterSet(NautobotFilterSet):
    class Meta:
        model = RoutingProtocol
        fields = ["routing_table", "protocol_type", "name", "slug"]


class RouteFilterSet(NautobotFilterSet):
    is_managed = django_filters.BooleanFilter()

    class Meta:
        model = Route
        fields = ["routing_table", "prefix", "protocol", "is_managed"]
