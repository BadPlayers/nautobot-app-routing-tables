from types import SimpleNamespace
from unittest.mock import MagicMock

from nautobot_routing_tables.models import RoutingTable


class DummyObject(SimpleNamespace):
    def __init__(self, label=None, **kwargs):
        super().__init__(**kwargs)
        self._label = label or kwargs.get("name") or self.__class__.__name__

    def __str__(self):
        return self._label


def make_vrf(label="VRF-A", prefix_matches=True):
    prefixes = MagicMock()
    prefixes.filter.return_value.exists.return_value = prefix_matches
    return DummyObject(label=label, prefixes=prefixes, name=label)


def make_prefix(value, pk=1, vrf=None):
    return DummyObject(label=value, pk=pk, prefix=value, vrf=vrf, _meta=DummyObject(label_lower="ipam.prefix"))


def make_ip_address(value):
    return DummyObject(label=value, pk=101, address=f"{value}/32", _meta=DummyObject(label_lower="ipam.ipaddress"))


def make_prefix_next_hop(value):
    return DummyObject(label=value, pk=102, prefix=value, _meta=DummyObject(label_lower="ipam.prefix"))


def make_interface(label):
    return DummyObject(label=label, pk=103, device_id=1, name=label, _meta=DummyObject(label_lower="dcim.interface"))


def make_routing_table(device="device-1", vrf=None):
    routing_table = RoutingTable(device_id=1, vrf_id=1 if vrf is not None else None)
    routing_table._state.fields_cache["device"] = DummyObject(label=device, id=1, name=device)
    if vrf is not None:
        routing_table._state.fields_cache["vrf"] = vrf
    return routing_table


def set_cached_relation(instance, field_name, value):
    instance._state.fields_cache[field_name] = value
    return value
