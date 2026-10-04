"""Filter sets shared by the UI and REST API."""

import django_filters
from nautobot.apps.filters import NautobotFilterSet

from .models import Route, RoutingProtocol, RoutingTable


class RoutingTableFilterSet(NautobotFilterSet):
    """Filter tables by device and routing context."""

    class Meta:
        """Declare framework metadata."""

        model = RoutingTable
        fields = ["device", "vrf"]


class RoutingProtocolFilterSet(NautobotFilterSet):
    """Filter protocol preferences by table, protocol and distance."""

    class Meta:
        """Declare framework metadata."""

        model = RoutingProtocol
        fields = ["routing_table", "protocol", "admin_distance_override"]


class RouteFilterSet(NautobotFilterSet):
    """Filter routes by table, destination, protocol and ownership."""

    is_managed = django_filters.BooleanFilter()

    class Meta:
        """Declare framework metadata."""

        model = Route
        fields = ["routing_table", "prefix", "protocol", "is_managed"]
