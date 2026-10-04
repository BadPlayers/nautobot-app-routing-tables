"""Route reconciliation and validated, lossless CSV interchange."""

from __future__ import annotations

import csv
import io
import ipaddress
import json
from dataclasses import dataclass
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.db import transaction
from nautobot.dcim.models import Cable, Device, Interface
from nautobot.extras.models import Status
from nautobot.ipam.models import VRF, IPAddress, Namespace, Prefix

from .models import Route, RoutingProtocol, RoutingTable
from .utils import get_setting

CSV_TEMPLATE_HEADER = "device,vrf,prefix,protocol,next_hop,metric,admin_distance,admin_distance_override,parameters,is_managed,source_interface,namespace\n"


@dataclass(frozen=True)
class ConnectedRouteCandidate:
    """An interface network in its routing context."""

    vrf: VRF | None
    network: ipaddress.IPv4Network | ipaddress.IPv6Network
    interface: Interface
    namespace: Namespace


def connected_routes_enabled() -> bool:
    """Return whether automatic reconciliation is enabled."""
    return bool(get_setting("AUTO_MANAGE_CONNECTED_ROUTES", True))


def _interface_is_admin_up(interface):
    return bool(getattr(interface, "enabled", True))


def _interface_is_cabled_up(interface):
    if not get_setting("REQUIRE_CABLE_FOR_CONNECTED_ROUTES", True):
        return True
    if hasattr(Interface, "cable_termination"):
        return getattr(interface, "cable_termination", None) is not None
    return interface.cable_id is not None


def interfaces_for_cable(cable_id, using="default"):
    """Support both direct cable fields and Nautobot 3.2 cable assignments."""
    field = "cable_termination__cable_id" if hasattr(Interface, "cable_termination") else "cable_id"
    return Interface.objects.using(using).filter(**{field: cable_id})


def _connected_candidates_for_interface(interface):
    if (
        interface is None
        or interface.pk is None
        or not _interface_is_admin_up(interface)
        or not _interface_is_cabled_up(interface)
    ):
        return []
    candidates = {}
    for ip in interface.ip_addresses.select_related("parent__namespace"):
        network = ipaddress.ip_interface(str(ip.address)).network
        if network.prefixlen == network.max_prefixlen:
            continue
        if interface.vrf_id and interface.vrf.namespace_id != ip.parent.namespace_id:
            continue
        key = (ip.parent.namespace_id, str(network))
        candidates[key] = ConnectedRouteCandidate(interface.vrf, network, interface, ip.parent.namespace)
    return list(candidates.values())


def _get_or_create_prefix(vrf, network, namespace):
    prefix = Prefix.objects.filter(namespace=namespace, prefix=str(network)).first()
    if prefix is None:
        if not get_setting("AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES", True):
            raise Prefix.DoesNotExist(str(network))
        prefix = Prefix.objects.create(
            prefix=str(network), namespace=namespace, status=Status.objects.get(name="Active")
        )
    if vrf is not None:
        prefix.vrfs.add(vrf)
    elif prefix.vrfs.exists():
        raise Prefix.DoesNotExist("Prefix is assigned to a VRF")
    return prefix


@transaction.atomic
def reconcile_connected_routes_for_interface(interface):
    """Synchronize only the connected routes owned by this interface."""
    if not connected_routes_enabled() or interface is None or interface.pk is None:
        return
    interface = (
        Interface.objects.select_for_update(of=("self",))
        .select_related("device", "vrf", "vrf__namespace")
        .filter(pk=interface.pk)
        .first()
    )
    if interface is None:
        return
    desired = set()
    interface_type = ContentType.objects.get_for_model(Interface)
    tables = {table.vrf_id: table for table in RoutingTable.objects.filter(device_id=interface.device_id)}
    for candidate in _connected_candidates_for_interface(interface):
        table = tables.get(interface.vrf_id)
        if table is None:
            continue
        try:
            prefix = _get_or_create_prefix(candidate.vrf, candidate.network, candidate.namespace)
        except Prefix.DoesNotExist:
            continue
        route, _ = Route.objects.get_or_create(
            routing_table=table,
            prefix=prefix,
            protocol="connected",
            next_hop_type=interface_type,
            next_hop_id=interface.pk,
            defaults={"is_managed": True, "source_interface": interface, "metric": 0},
        )
        desired.add(route.pk)
    Route.objects.filter(is_managed=True, source_interface=interface, protocol="connected").exclude(
        pk__in=desired
    ).delete()


def reconcile_connected_routes_for_cable(cable: Cable | None):
    """Reconcile physical interfaces currently attached to a cable."""
    if connected_routes_enabled() and cable is not None:
        for interface in interfaces_for_cable(cable.pk).iterator():
            reconcile_connected_routes_for_interface(interface)


def reconcile_connected_routes_for_all_devices():
    """Reconcile interfaces without retaining the complete inventory in memory."""
    if connected_routes_enabled():
        for interface in Interface.objects.all().iterator(chunk_size=500):
            reconcile_connected_routes_for_interface(interface)


def prefixes_for_table(routing_table):
    """Scope prefixes by VRF membership, including the global routing context."""
    if routing_table.vrf_id:
        return Prefix.objects.filter(vrfs=routing_table.vrf)
    return Prefix.objects.filter(vrfs__isnull=True)


def _unique_match(queryset, description):
    matches = list(queryset[:2])
    if len(matches) > 1:
        raise ValueError(f"Ambiguous {description}; use an explicit object UUID or namespace.")
    return matches[0] if matches else None


def resolve_next_hop_value(routing_table, raw_value, namespace=None):
    """Resolve a typed UUID, interface name or IP value without arbitrary matches."""
    value = (raw_value or "").strip()
    if not value:
        return None
    explicit_type, _, lookup = value.partition(":")
    if explicit_type not in {"ip", "prefix", "interface"}:
        lookup, explicit_type = value, None
    lookup = lookup.strip()
    try:
        object_id = UUID(lookup)
    except ValueError:
        object_id = None
    if explicit_type in {None, "interface"}:
        interfaces = Interface.objects.filter(device_id=routing_table.device_id)
        match = _unique_match(interfaces.filter(**({"pk": object_id} if object_id else {"name": lookup})), "interface")
        if match:
            return match
    if explicit_type == "interface":
        raise ValueError(f"Unable to resolve next-hop '{raw_value}'.")
    try:
        address = ipaddress.ip_interface(lookup)
    except ValueError:
        if object_id is None:
            raise ValueError(f"Unable to resolve next-hop '{raw_value}'.") from None
        address = None
    if explicit_type in {None, "prefix"} and (object_id or "/" in lookup):
        prefixes = prefixes_for_table(routing_table)
        if namespace is not None:
            prefixes = prefixes.filter(namespace=namespace)
        if object_id:
            prefixes = prefixes.filter(pk=object_id)
        elif address.ip == address.network.network_address:
            prefixes = prefixes.filter(prefix=str(address.network))
        else:
            prefixes = prefixes.none()
        match = _unique_match(prefixes, "prefix")
        if match:
            return match
    if explicit_type in {None, "ip"}:
        ips = IPAddress.objects.filter(parent__in=prefixes_for_table(routing_table))
        if namespace is not None:
            ips = ips.filter(parent__namespace=namespace)
        ips = ips.filter(pk=object_id) if object_id else ips.filter(host=str(address.ip))
        if not object_id and "/" in lookup:
            ips = ips.filter(mask_length=address.network.prefixlen)
        match = _unique_match(ips, "IP address")
        if match:
            return match
    raise ValueError(f"Unable to resolve next-hop '{raw_value}'.")


def next_hop_csv_value(route):
    """Encode a next-hop without ambiguity between names, IPs and prefixes."""
    if route.next_hop is None:
        return ""
    kind = {"ipam.ipaddress": "ip", "ipam.prefix": "prefix", "dcim.interface": "interface"}[
        route.next_hop._meta.label_lower
    ]
    return f"{kind}:{route.next_hop.pk}"


def optimized_routes(queryset):
    """Load route display dependencies in bounded queries instead of per row."""
    return queryset.select_related(
        "routing_table__device",
        "routing_table__vrf",
        "prefix__namespace",
        "source_interface",
        "next_hop_type",
    ).prefetch_related("routing_table__protocol_overrides", "next_hop")


def export_routing_tables_as_csv(queryset):
    """Export routes with typed next-hops and namespace-qualified IPAM objects."""
    rows = io.StringIO(newline="")
    writer = csv.DictWriter(rows, fieldnames=CSV_TEMPLATE_HEADER.strip().split(","))
    writer.writeheader()
    for route in optimized_routes(queryset).iterator(chunk_size=500):
        override = route.protocol_override
        writer.writerow(
            {
                "device": route.routing_table.device.name,
                "vrf": route.routing_table.vrf.name if route.routing_table.vrf else "",
                "namespace": route.prefix.namespace.name,
                "prefix": route.prefix.prefix,
                "protocol": route.protocol,
                "next_hop": next_hop_csv_value(route),
                "metric": route.metric if route.metric is not None else "",
                "admin_distance": route.admin_distance if route.admin_distance is not None else "",
                "admin_distance_override": override.admin_distance_override if override else "",
                "parameters": json.dumps(override.parameters) if override else "",
                "is_managed": str(route.is_managed).lower(),
                "source_interface": route.source_interface.name if route.source_interface else "",
            }
        )
    return rows.getvalue()


@transaction.atomic
def import_routing_tables_from_csv(content):
    """Import atomically, validating rows and preserving omitted optional values."""
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True)
    required = {"device", "prefix", "protocol"}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("CSV requires device, prefix and protocol columns.")
    stats = {"routing_tables": 0, "routes": 0, "overrides": 0}
    for row in reader:
        try:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("Row has an incorrect number of columns.")
            row = {key: value.strip() for key, value in row.items()}
            namespace = Namespace.objects.get(name=row["namespace"]) if row.get("namespace") else None
            device = Device.objects.get(name=row["device"])
            vrfs = VRF.objects.filter(name=row.get("vrf", ""))
            if namespace:
                vrfs = vrfs.filter(namespace=namespace)
            vrf = vrfs.get() if row.get("vrf") else None
            table, created = RoutingTable.objects.get_or_create(device=device, vrf=vrf)
            stats["routing_tables"] += int(created)
            protocol = row["protocol"]
            if row.get("admin_distance_override"):
                override, created = RoutingProtocol.objects.get_or_create(
                    routing_table=table,
                    protocol=protocol,
                    defaults={"admin_distance_override": int(row["admin_distance_override"])},
                )
                override.admin_distance_override = int(row["admin_distance_override"])
                if row.get("parameters"):
                    override.parameters = json.loads(row["parameters"])
                override.validated_save()
                stats["overrides"] += int(created)
            prefixes = prefixes_for_table(table).filter(prefix=row["prefix"])
            if namespace:
                prefixes = prefixes.filter(namespace=namespace)
            prefix = prefixes.get()
            managed = row.get("is_managed", "").lower()
            if managed not in {"", "true", "false"}:
                raise ValueError("is_managed must be true or false.")
            route = Route(
                routing_table=table,
                prefix=prefix,
                protocol=protocol,
                metric=int(row["metric"]) if row.get("metric") else None,
                admin_distance=int(row["admin_distance"]) if row.get("admin_distance") else None,
                is_managed=managed == "true",
            )
            if row.get("source_interface"):
                route.source_interface = Interface.objects.get(device=device, name=row["source_interface"])
            route.next_hop = resolve_next_hop_value(table, row.get("next_hop", ""), namespace=prefix.namespace)
            route.validated_save()
            stats["routes"] += 1
        except (ValueError, ValidationError, ObjectDoesNotExist, MultipleObjectsReturned) as exc:
            raise ValueError(f"CSV row {reader.line_num}: {exc}") from exc
    return stats
