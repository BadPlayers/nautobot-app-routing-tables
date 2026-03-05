from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Optional

from django.db import transaction

from nautobot.dcim.models import Cable, Interface
from nautobot.ipam.models import IPAddress, Prefix, VRF

from .models import ProtocolType, Route, RoutingProtocol, RoutingTable
from .utils import get_setting


@dataclass(frozen=True)
class ConnectedRouteCandidate:
    vrf: VRF
    network: ipaddress._BaseNetwork
    interface: Interface


def connected_routes_enabled() -> bool:
    return bool(get_setting("AUTO_MANAGE_CONNECTED_ROUTES", True))


def _interface_is_admin_up(interface: Interface) -> bool:
    return bool(getattr(interface, "enabled", True))


def _interface_is_cabled_up(interface: Interface) -> bool:
    if not get_setting("REQUIRE_CABLE_FOR_CONNECTED_ROUTES", True):
        return True
    return getattr(interface, "cable", None) is not None


def _connected_candidates_for_interface(interface: Interface) -> list[ConnectedRouteCandidate]:
    if interface is None or interface.pk is None:
        return []
    if not _interface_is_admin_up(interface):
        return []
    if not _interface_is_cabled_up(interface):
        return []

    ip_qs = IPAddress.objects.filter(assigned_object_type__model="interface", assigned_object_id=interface.pk)
    candidates: list[ConnectedRouteCandidate] = []
    for ip in ip_qs:
        try:
            ipi = ipaddress.ip_interface(str(ip.address))
        except Exception:
            continue
        if ipi.network.prefixlen in (32, 128):
            continue
        vrf = ip.vrf
        if vrf is None:
            continue
        candidates.append(ConnectedRouteCandidate(vrf=vrf, network=ipi.network, interface=interface))
    return candidates


def _get_or_create_prefix(vrf: VRF, network: ipaddress._BaseNetwork) -> Prefix:
    prefix_str = str(network)
    prefix = Prefix.objects.filter(vrf=vrf, prefix=prefix_str).first()
    if prefix:
        return prefix
    if not get_setting("AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES", True):
        raise Prefix.DoesNotExist(prefix_str)
    return Prefix.objects.create(prefix=prefix_str, vrf=vrf, status="active")


def _get_connected_protocol(routing_table: RoutingTable) -> RoutingProtocol:
    connected_slug = get_setting("CONNECTED_ROUTE_PROTOCOL_SLUG", "connected")
    pt, _ = ProtocolType.objects.get_or_create(name="Connected", defaults={"slug": connected_slug})
    if pt.slug != connected_slug:
        pt.slug = connected_slug
        pt.save()

    proto, _ = RoutingProtocol.objects.get_or_create(
        routing_table=routing_table,
        slug="connected",
        defaults={"name": "Connected", "protocol_type": pt},
    )
    if proto.protocol_type_id != pt.id:
        proto.protocol_type = pt
        proto.save()
    return proto


@transaction.atomic
def reconcile_connected_routes_for_interface(interface: Interface) -> None:
    if not connected_routes_enabled():
        return
    if interface is None or interface.pk is None:
        return

    desired_keys: set[tuple[int, int]] = set()  # (routing_table_id, prefix_id)

    for cand in _connected_candidates_for_interface(interface):
        rt = RoutingTable.objects.filter(device=interface.device, vrf=cand.vrf).first()
        if not rt:
            continue
        proto = _get_connected_protocol(rt)
        try:
            prefix = _get_or_create_prefix(cand.vrf, cand.network)
        except Prefix.DoesNotExist:
            continue

        desired_keys.add((rt.id, prefix.id))
        Route.objects.get_or_create(
            routing_table=rt,
            prefix=prefix,
            protocol=proto,
            defaults={
                "is_managed": True,
                "source_interface": interface,
                "metric": 0,
                "admin_distance": proto.effective_admin_distance(),
            },
        )

    for route in Route.objects.filter(is_managed=True, source_interface=interface):
        if (route.routing_table_id, route.prefix_id) not in desired_keys:
            route.delete()


def reconcile_connected_routes_for_cable(cable: Optional[Cable]) -> None:
    if not connected_routes_enabled():
        return
    if cable is None:
        return
    for iface in Interface.objects.filter(cable=cable):
        reconcile_connected_routes_for_interface(iface)


def reconcile_connected_routes_for_all_devices() -> None:
    if not connected_routes_enabled():
        return
    for iface in Interface.objects.select_related("device").all():
        reconcile_connected_routes_for_interface(iface)
