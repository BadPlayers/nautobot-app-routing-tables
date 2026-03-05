import django_tables2 as tables
from nautobot.apps.tables import BaseTable

from .models import ProtocolType, Route, RoutingProtocol, RoutingTable


class ProtocolTypeTable(BaseTable):
    name = tables.Column(linkify=True)

    class Meta(BaseTable.Meta):
        model = ProtocolType
        fields = ("pk", "name", "slug", "default_admin_distance", "created", "last_updated")


class RoutingTableTable(BaseTable):
    name = tables.Column(linkify=True)

    class Meta(BaseTable.Meta):
        model = RoutingTable
        fields = ("pk", "name", "device", "vrf", "created", "last_updated")


class RoutingProtocolTable(BaseTable):
    name = tables.Column(linkify=True)

    class Meta(BaseTable.Meta):
        model = RoutingProtocol
        fields = ("pk", "name", "routing_table", "protocol_type", "admin_distance_override", "created", "last_updated")


class RouteTable(BaseTable):
    prefix = tables.Column(linkify=True)

    class Meta(BaseTable.Meta):
        model = Route
        fields = (
            "pk",
            "routing_table",
            "prefix",
            "protocol",
            "next_hop_ip",
            "next_hop_interface",
            "metric",
            "admin_distance",
            "is_managed",
            "source_interface",
            "created",
            "last_updated",
        )
