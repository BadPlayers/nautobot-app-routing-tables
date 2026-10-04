"""Regression tests for CSV interchange and connected-route reconciliation."""

import csv
import io
from unittest.mock import patch

from django.db import connection
from django.test.utils import CaptureQueriesContext
from nautobot.dcim.models import Interface
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_routing_tables import services
from nautobot_routing_tables.models import Route, RoutingProtocol
from nautobot_routing_tables.tests.base import RoutingTestCase


class RoutingServicesTestCase(RoutingTestCase):
    def route(self, **kwargs):
        defaults = dict(routing_table=self.table, prefix=self.prefix, protocol="static", metric=0)
        defaults.update(kwargs)
        obj = Route(**defaults)
        obj.validated_save()
        return obj

    def test_resolve_next_hops(self):
        for value, expected in (
            ("Ethernet1", self.interface),
            ("interface:Ethernet1", self.interface),
            ("192.0.2.1", self.ip),
            ("ip:192.0.2.1/24", self.ip),
            ("prefix:192.0.2.0/24", self.transit),
            (f"ip:{self.ip.pk}", self.ip),
        ):
            with self.subTest(value=value):
                self.assertEqual(services.resolve_next_hop_value(self.table, value), expected)
        self.assertIsNone(services.resolve_next_hop_value(self.table, " "))
        for value in ("missing", "interface:missing", "ip:192.0.2.9", "prefix:192.0.2.3/24"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                services.resolve_next_hop_value(self.table, value)

    def test_next_hop_cannot_resolve_another_vrf(self):
        with self.assertRaises(ValueError):
            services.resolve_next_hop_value(self.global_table, "192.0.2.1")

    def test_csv_round_trip_preserves_uuid_zero_and_parameters(self):
        RoutingProtocol.objects.create(
            routing_table=self.table,
            protocol="static",
            admin_distance_override=0,
            parameters={"text": "line1\nline2", "comma": ","},
        )
        route = self.route(next_hop=self.ip, admin_distance=0)
        exported = services.export_routing_tables_as_csv(Route.objects.filter(pk=route.pk))
        row = next(csv.DictReader(io.StringIO(exported)))
        self.assertEqual(row["metric"], "0")
        self.assertEqual(row["next_hop"], f"ip:{self.ip.pk}")
        route.delete()
        stats = services.import_routing_tables_from_csv(exported.encode())
        self.assertEqual(stats["routes"], 1)
        restored = Route.objects.get()
        self.assertEqual(restored.next_hop, self.ip)
        self.assertEqual(restored.metric, 0)
        self.assertEqual(restored.admin_distance, 0)
        self.assertEqual(restored.protocol_override.parameters["text"], "line1\nline2")

    def test_csv_optional_columns_and_bom(self):
        data = "\ufeffdevice,vrf,prefix,protocol\nleaf-1,BLUE,10.10.0.0/24,static\n"
        self.assertEqual(services.import_routing_tables_from_csv(data.encode())["routes"], 1)

    def test_csv_invalid_rows_roll_back(self):
        for suffix in ("leaf-1,BLUE,10.10.0.0/24,invalid", "missing,BLUE,10.10.0.0/24,static"):
            data = f"device,vrf,prefix,protocol\nleaf-1,BLUE,10.10.0.0/24,static\n{suffix}\n"
            with self.subTest(suffix=suffix), self.assertRaisesRegex(ValueError, "CSV row 3"):
                services.import_routing_tables_from_csv(data.encode())
            self.assertFalse(Route.objects.exists())
        for data in (b"wrong\n", b"device,prefix,protocol\nleaf-1,10.10.0.0/24\n"):
            with self.assertRaises(ValueError):
                services.import_routing_tables_from_csv(data)

    def test_csv_override_validation_rolls_back(self):
        with self.assertRaises(ValueError):
            services.import_routing_tables_from_csv(
                b"device,vrf,prefix,protocol,admin_distance_override\nleaf-1,BLUE,10.10.0.0/24,static,999\n"
            )
        self.assertFalse(RoutingProtocol.objects.exists())

    def test_csv_rejects_invalid_boolean(self):
        with self.assertRaisesRegex(ValueError, "is_managed"):
            services.import_routing_tables_from_csv(
                b"device,vrf,prefix,protocol,is_managed\nleaf-1,BLUE,10.10.0.0/24,static,yes\n"
            )

    def test_export_queries_do_not_grow_per_route(self):
        self.route(next_hop=self.ip)
        RoutingProtocol.objects.create(routing_table=self.table, protocol="static", admin_distance_override=5)
        # Warm ContentType caches before comparing query counts.
        services.export_routing_tables_as_csv(Route.objects.all())
        with CaptureQueriesContext(connection) as one:
            services.export_routing_tables_as_csv(Route.objects.all())
        for protocol in ("ospf", "rip", "ibgp", "ebgp"):
            self.route(protocol=protocol, next_hop=self.ip)
        with CaptureQueriesContext(connection) as many:
            services.export_routing_tables_as_csv(Route.objects.all())
        self.assertEqual(len(one), len(many))
        self.assertLessEqual(len(many), 4)

    @patch(
        "nautobot_routing_tables.services.get_setting",
        side_effect=lambda name, fallback: name != "REQUIRE_CABLE_FOR_CONNECTED_ROUTES",
    )
    def test_connected_routes_idempotence_and_cleanup(self, _settings):
        services.reconcile_connected_routes_for_interface(self.interface)
        services.reconcile_connected_routes_for_interface(self.interface)
        route = Route.objects.get()
        self.assertEqual(route.prefix, self.transit)
        self.assertEqual(route.next_hop, self.interface)
        self.assertEqual(route.metric, 0)
        manual = self.route(protocol="connected")
        self.interface.enabled = False
        self.interface.save()
        services.reconcile_connected_routes_for_interface(self.interface)
        self.assertEqual(list(Route.objects.all()), [manual])

    @patch(
        "nautobot_routing_tables.services.get_setting",
        side_effect=lambda name, fallback: name != "REQUIRE_CABLE_FOR_CONNECTED_ROUTES",
    )
    def test_shared_subnet_routes_keep_separate_interface_ownership(self, _settings):
        other = Interface.objects.create(
            device=self.device, name="Ethernet2", type="1000base-t", status=self.active, vrf=self.vrf
        )
        other.ip_addresses.add(self.ip)
        services.reconcile_connected_routes_for_interface(self.interface)
        services.reconcile_connected_routes_for_interface(other)
        self.assertEqual(Route.objects.count(), 2)
        other.ip_addresses.clear()
        services.reconcile_connected_routes_for_interface(other)
        self.assertEqual(Route.objects.get().source_interface, self.interface)

    @patch(
        "nautobot_routing_tables.services.get_setting",
        side_effect=lambda name, fallback: name != "REQUIRE_CABLE_FOR_CONNECTED_ROUTES",
    )
    def test_global_and_ipv6_connected_routes(self, _settings):
        network = Prefix.objects.create(prefix="2001:db8::/64", namespace=self.namespace, status=self.active)
        ip = IPAddress.objects.create(address="2001:db8::1/64", parent=network, status=self.active)
        self.interface.vrf = None
        self.interface.save()
        self.interface.ip_addresses.set([ip])
        services.reconcile_connected_routes_for_interface(self.interface)
        route = Route.objects.get()
        self.assertEqual(route.routing_table, self.global_table)
        self.assertEqual(route.prefix, network)

    def test_auto_create_prefix_and_disabled_policy(self):
        import ipaddress

        with (
            patch("nautobot_routing_tables.services.get_setting", return_value=False),
            self.assertRaises(Prefix.DoesNotExist),
        ):
            services._get_or_create_prefix(self.vrf, ipaddress.ip_network("192.0.2.0/25"), self.namespace)
        with patch("nautobot_routing_tables.services.get_setting", return_value=True):
            prefix = services._get_or_create_prefix(self.vrf, ipaddress.ip_network("192.0.2.0/25"), self.namespace)
        self.assertTrue(prefix.vrfs.filter(pk=self.vrf.pk).exists())

    def test_no_cable_or_disabled_reconciliation(self):
        with patch("nautobot_routing_tables.services.connected_routes_enabled", return_value=True):
            services.reconcile_connected_routes_for_interface(self.interface)
        self.assertFalse(Route.objects.exists())

    def test_ambiguous_global_prefix_is_rejected(self):
        for name in ("A", "B"):
            ns = Namespace.objects.create(name=name)
            Prefix.objects.create(prefix="203.0.113.0/24", namespace=ns, status=self.active)
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            services.resolve_next_hop_value(self.global_table, "prefix:203.0.113.0/24")

    @patch(
        "nautobot_routing_tables.services.get_setting",
        side_effect=lambda name, fallback: name != "REQUIRE_CABLE_FOR_CONNECTED_ROUTES",
    )
    def test_host_routes_are_skipped(self, _settings):
        self.ip.mask_length = 32
        self.ip.save()
        services.reconcile_connected_routes_for_interface(self.interface)
        self.assertFalse(Route.objects.exists())

    @patch(
        "nautobot_routing_tables.services.get_setting",
        side_effect=lambda name, fallback: name != "REQUIRE_CABLE_FOR_CONNECTED_ROUTES",
    )
    def test_interface_namespace_mismatch_is_skipped(self, _settings):
        from nautobot.ipam.models import VRF

        ns = Namespace.objects.create(name="Other")
        self.interface.vrf = VRF.objects.create(name="Other", namespace=ns)
        self.interface.save()
        services.reconcile_connected_routes_for_interface(self.interface)
        self.assertFalse(Route.objects.exists())

    @patch(
        "nautobot_routing_tables.services.get_setting",
        side_effect=lambda name, fallback: name != "REQUIRE_CABLE_FOR_CONNECTED_ROUTES",
    )
    def test_reconcile_missing_table_or_deleted_interface(self, _settings):
        self.table.delete()
        services.reconcile_connected_routes_for_interface(self.interface)
        self.assertFalse(Route.objects.exists())
        from uuid import uuid4

        services.reconcile_connected_routes_for_interface(Interface(pk=uuid4()))
        services.reconcile_connected_routes_for_interface(None)

    @patch(
        "nautobot_routing_tables.services.get_setting",
        side_effect=lambda name, fallback: name == "AUTO_MANAGE_CONNECTED_ROUTES",
    )
    def test_reconcile_missing_prefix_with_creation_disabled(self, _settings):
        self.ip.mask_length = 25
        self.ip.save()
        services.reconcile_connected_routes_for_interface(self.interface)
        self.assertFalse(Route.objects.exists())

    def test_global_prefix_lookup_does_not_steal_vrf_prefix(self):
        import ipaddress

        with self.assertRaises(Prefix.DoesNotExist):
            services._get_or_create_prefix(None, ipaddress.ip_network("192.0.2.0/24"), self.namespace)

    def test_csv_managed_interface_and_no_next_hop(self):
        route = self.route(protocol="connected", is_managed=True, source_interface=self.interface)
        exported = services.export_routing_tables_as_csv(Route.objects.all())
        route.delete()
        services.import_routing_tables_from_csv(exported.encode())
        self.assertEqual(Route.objects.get().source_interface, self.interface)

    def test_typed_prefix_uuid_and_namespace_lookup(self):
        self.assertEqual(
            services.resolve_next_hop_value(self.table, f"prefix:{self.transit.pk}", namespace=self.namespace),
            self.transit,
        )

    @patch("nautobot_routing_tables.services.reconcile_connected_routes_for_interface")
    @patch("nautobot_routing_tables.services.connected_routes_enabled", return_value=True)
    def test_inventory_reconciliation_streams_interfaces(self, _enabled, reconcile):
        services.reconcile_connected_routes_for_all_devices()
        reconcile.assert_called_once_with(self.interface)
