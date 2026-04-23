import django_filters
from nautobot.apps.filters import NautobotFilterSet

from .models import Route, RoutingProtocol, RoutingTable


class RoutingTableFilterSet(NautobotFilterSet):
    class Meta:
        model = RoutingTable
        fields = ["device", "vrf"]


class RoutingProtocolFilterSet(NautobotFilterSet):
    class Meta:
        model = RoutingProtocol
        fields = ["routing_table", "protocol", "admin_distance_override"]


class RouteFilterSet(NautobotFilterSet):
    is_managed = django_filters.BooleanFilter()

    class Meta:
        model = Route
        fields = ["routing_table", "prefix", "protocol", "is_managed"]
