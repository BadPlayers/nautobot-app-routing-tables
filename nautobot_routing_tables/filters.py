"""Filter sets shared by the UI and REST API."""

import django_filters
from django.db.models import Q
from nautobot.apps.filters import NautobotFilterSet

from .models import Route, RoutingProtocol, RoutingTable


class RoutingTableFilterSet(NautobotFilterSet):
    """Filter tables by device and routing context."""

    q = django_filters.CharFilter(method="search")

    def search(self, queryset, name, value):
        """Search the human-readable device and VRF rather than UUIDs."""
        return queryset.filter(Q(device__name__icontains=value) | Q(vrf__name__icontains=value))

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
