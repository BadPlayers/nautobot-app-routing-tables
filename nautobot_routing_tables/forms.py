from nautobot.apps.forms import NautobotModelForm

from .models import ProtocolType, Route, RoutingProtocol, RoutingTable


class ProtocolTypeForm(NautobotModelForm):
    class Meta:
        model = ProtocolType
        fields = ["name", "slug", "default_admin_distance"]


class RoutingTableForm(NautobotModelForm):
    class Meta:
        model = RoutingTable
        fields = ["name", "slug", "device", "vrf"]


class RoutingProtocolForm(NautobotModelForm):
    class Meta:
        model = RoutingProtocol
        fields = ["name", "slug", "routing_table", "protocol_type", "admin_distance_override", "parameters"]


class RouteForm(NautobotModelForm):
    class Meta:
        model = Route
        fields = [
            "routing_table",
            "prefix",
            "protocol",
            "next_hop_ip",
            "next_hop_interface",
            "metric",
            "admin_distance",
            "is_managed",
            "source_interface",
        ]
