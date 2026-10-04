"""REST representations and validated polymorphic next-hop references."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from nautobot.apps.api import ContentTypeField, NautobotModelSerializer
from rest_framework import serializers

from ..models import Route, RoutingProtocol, RoutingTable


class RoutingTableSerializer(NautobotModelSerializer):
    """Serialize routing table fields and relationships."""

    class Meta:
        """Declare framework metadata."""

        model = RoutingTable
        fields = "__all__"


class RoutingProtocolSerializer(NautobotModelSerializer):
    """Expose protocol overrides alongside their default distance."""

    default_admin_distance = serializers.IntegerField(read_only=True)

    class Meta:
        """Declare framework metadata."""

        model = RoutingProtocol
        fields = "__all__"


class RouteSerializer(NautobotModelSerializer):
    """Serialize routes with UUID next-hops and resolved distances."""

    next_hop_type = ContentTypeField(
        queryset=ContentType.objects.filter(
            Q(app_label="ipam", model__in=("ipaddress", "prefix")) | Q(app_label="dcim", model="interface")
        ),
        required=False,
        allow_null=True,
    )
    next_hop_display = serializers.CharField(read_only=True)
    resolved_admin_distance = serializers.IntegerField(read_only=True)

    class Meta:
        """Declare framework metadata."""

        model = Route
        fields = "__all__"
