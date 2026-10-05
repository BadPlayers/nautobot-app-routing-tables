"""Shared routing-context querysets for assisted route entry."""

from django.core.exceptions import ValidationError
from nautobot.dcim.models import Interface
from nautobot.ipam.models import IPAddress, Prefix

from .models import RoutingTable
from .services import prefixes_for_table


def selected_table(value):
    """Resolve an optional form value without raising on malformed input."""
    if isinstance(value, RoutingTable):
        return value
    try:
        return RoutingTable.objects.select_related("device", "vrf").filter(pk=value).first() if value else None
    except (ValueError, ValidationError):
        return None


def routing_choices(kind, table, destination=None):
    """Return choices compatible with the table and destination address family."""
    model = {"ip": IPAddress, "prefix": Prefix, "interface": Interface}.get(kind, IPAddress)
    if table is None:
        return model.objects.none()
    if kind == "interface":
        return Interface.objects.filter(device_id=table.device_id).select_related("device")
    prefixes = prefixes_for_table(table)
    queryset = (
        prefixes.select_related("namespace")
        if kind == "prefix"
        else IPAddress.objects.filter(parent__in=prefixes).select_related("parent__namespace")
    )
    if destination is not None:
        queryset = queryset.filter(ip_version=destination.ip_version)
    return queryset


def choice_label(obj):
    """Include namespace or device information in otherwise ambiguous labels."""
    if isinstance(obj, Interface):
        return f"{obj.device} / {obj.name}"
    if isinstance(obj, IPAddress):
        return f"{obj.address} ({obj.parent.namespace})"
    return f"{obj.prefix} ({obj.namespace})"
