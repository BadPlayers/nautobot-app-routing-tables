import django_tables2 as tables
from nautobot.apps.tables import BaseTable, ButtonsColumn, ToggleColumn

from .models import Route, RoutingProtocol, RoutingTable


class RoutingTableTable(BaseTable):
    pk = ToggleColumn()
    device = tables.Column(linkify=True, verbose_name="Device")
    vrf = tables.Column(linkify=True, verbose_name="VRF")
    actions = ButtonsColumn(RoutingTable, verbose_name="")

    class Meta(BaseTable.Meta):
        model = RoutingTable
        fields = ("pk", "device", "vrf", "actions")
        default_columns = ("pk", "device", "vrf", "actions")


class RoutingProtocolTable(BaseTable):
    pk = ToggleColumn()
    protocol = tables.Column(verbose_name="Protocol")
    routing_table = tables.Column(linkify=True, verbose_name="Routing Table")
    default_admin_distance = tables.Column(verbose_name="Default Distance")
    admin_distance_override = tables.Column(verbose_name="Override")
    actions = ButtonsColumn(RoutingProtocol, verbose_name="")

    class Meta(BaseTable.Meta):
        model = RoutingProtocol
        fields = ("pk", "protocol", "routing_table", "default_admin_distance", "admin_distance_override", "actions")
        default_columns = ("pk", "protocol", "routing_table", "default_admin_distance", "admin_distance_override", "actions")


class RoutingTableDetailProtocolTable(BaseTable):
    protocol = tables.Column(verbose_name="Protocol")
    default_admin_distance = tables.Column(verbose_name="Default Distance")
    admin_distance_override = tables.Column(verbose_name="Override")
    actions = ButtonsColumn(RoutingProtocol, verbose_name="")

    class Meta(BaseTable.Meta):
        model = RoutingProtocol
        fields = ("protocol", "default_admin_distance", "admin_distance_override", "actions")
        default_columns = ("protocol", "default_admin_distance", "admin_distance_override", "actions")


class RouteTable(BaseTable):
    pk = ToggleColumn()
    routing_table = tables.Column(linkify=True, verbose_name="Routing Table")
    prefix = tables.Column(linkify=True, verbose_name="Prefix")
    protocol = tables.Column(verbose_name="Protocol")
    next_hop_display = tables.Column(empty_values=(), verbose_name="Next-hop")
    admin_distance = tables.Column(empty_values=(), verbose_name="Distance")
    metric = tables.Column(verbose_name="Metric")
    is_managed = tables.BooleanColumn(verbose_name="Managed")
    source_interface = tables.Column(linkify=True, verbose_name="Source Intf")
    actions = ButtonsColumn(Route, verbose_name="")

    def render_admin_distance(self, record):
        return record.resolved_admin_distance

    class Meta(BaseTable.Meta):
        model = Route
        fields = (
            "pk",
            "routing_table",
            "prefix",
            "protocol",
            "next_hop_display",
            "admin_distance",
            "metric",
            "is_managed",
            "source_interface",
            "actions",
        )
        default_columns = (
            "pk",
            "routing_table",
            "prefix",
            "protocol",
            "next_hop_display",
            "admin_distance",
            "metric",
            "is_managed",
            "source_interface",
            "actions",
        )


class RoutingTableDetailRouteTable(BaseTable):
    prefix = tables.Column(linkify=True, verbose_name="Prefix")
    protocol = tables.Column(verbose_name="Protocol")
    next_hop_display = tables.Column(empty_values=(), verbose_name="Next-hop")
    admin_distance = tables.Column(empty_values=(), verbose_name="Distance")
    metric = tables.Column(verbose_name="Metric")
    is_managed = tables.BooleanColumn(verbose_name="Managed")
    actions = ButtonsColumn(Route, verbose_name="")

    def render_admin_distance(self, record):
        return record.resolved_admin_distance

    class Meta(BaseTable.Meta):
        model = Route
        fields = ("prefix", "protocol", "next_hop_display", "admin_distance", "metric", "is_managed", "actions")
        default_columns = ("prefix", "protocol", "next_hop_display", "admin_distance", "metric", "is_managed", "actions")
