from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from nautobot_routing_tables import services


class RoutingServicesTestCase(SimpleTestCase):
    @patch("nautobot_routing_tables.services.Interface.objects.filter")
    def test_resolve_next_hop_prefers_local_interface(self, interface_filter):
        interface = SimpleNamespace(pk=1, name="Ethernet1")
        interface_filter.return_value.first.return_value = interface

        result = services.resolve_next_hop_value(SimpleNamespace(device="device-1", vrf=None), "Ethernet1")

        self.assertIs(result, interface)

    @patch("nautobot_routing_tables.services.Prefix.objects.filter")
    @patch("nautobot_routing_tables.services.Interface.objects.filter")
    def test_resolve_next_hop_finds_prefix(self, interface_filter, prefix_filter):
        interface_filter.return_value.first.return_value = None
        prefix = SimpleNamespace(pk=2, prefix="10.0.0.0/31")
        prefix_filter.return_value.first.return_value = prefix

        result = services.resolve_next_hop_value(SimpleNamespace(device="device-1", vrf=None), "prefix:10.0.0.0/31")

        self.assertIs(result, prefix)

    @patch("nautobot_routing_tables.services.IPAddress.objects.filter")
    @patch("nautobot_routing_tables.services.Prefix.objects.filter")
    @patch("nautobot_routing_tables.services.Interface.objects.filter")
    def test_resolve_next_hop_finds_ip_address(self, interface_filter, prefix_filter, ip_filter):
        interface_filter.return_value.first.return_value = None
        prefix_filter.return_value.first.return_value = None
        ip_address = SimpleNamespace(pk=3, address="10.0.0.1/32")
        ip_filter.return_value.first.return_value = ip_address

        result = services.resolve_next_hop_value(SimpleNamespace(device="device-1", vrf=None), "10.0.0.1")

        self.assertIs(result, ip_address)

    @patch("nautobot_routing_tables.services.RoutingProtocol.objects.filter")
    def test_export_routing_tables_as_csv_includes_override(self, protocol_filter):
        protocol_filter.return_value.first.return_value = SimpleNamespace(admin_distance_override=250, parameters={"tag": 10})
        route = SimpleNamespace(
            routing_table=SimpleNamespace(device=SimpleNamespace(name="leaf-1"), vrf=None),
            prefix=SimpleNamespace(prefix="0.0.0.0/0"),
            protocol="static",
            next_hop_display="10.0.0.1",
            next_hop=True,
            metric=10,
            admin_distance=1,
            is_managed=False,
            source_interface=None,
        )
        queryset = Mock()
        queryset.select_related.return_value = [route]

        csv_output = services.export_routing_tables_as_csv(queryset)

        self.assertIn("leaf-1", csv_output)
        self.assertIn("250", csv_output)
