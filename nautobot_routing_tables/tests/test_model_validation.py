"""Database model validation covers malformed routes and defaults."""

from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from nautobot.ipam.models import Prefix

from nautobot_routing_tables.models import Route, RoutingProtocol
from nautobot_routing_tables.services import optimized_routes
from nautobot_routing_tables.tests.base import RoutingTestCase


class RouteValidationTestCase(RoutingTestCase):
    def route(self, **kwargs):
        values = dict(routing_table=self.table, prefix=self.prefix, protocol="static")
        values.update(kwargs)
        return Route(**values)

    def test_distance_precedence_and_prefetch(self):
        self.assertIsNone(Route().protocol_override)
        route = self.route()
        self.assertEqual(route.resolved_admin_distance, 1)
        RoutingProtocol.objects.create(routing_table=self.table, protocol="static", admin_distance_override=8)
        self.assertEqual(route.resolved_admin_distance, 8)
        route.admin_distance = 0
        self.assertEqual(route.resolved_admin_distance, 0)
        route.save()
        with self.assertNumQueries(2):
            loaded = optimized_routes(Route.objects.all()).get()
        with self.assertNumQueries(0):
            self.assertEqual(loaded.protocol_override.admin_distance_override, 8)
        self.assertEqual(route.next_hop_display, "-")

    def test_global_and_vrf_membership_validation(self):
        route = self.route(routing_table=self.global_table)
        with self.assertRaises(ValidationError):
            route.clean()
        self.prefix.vrfs.clear()
        route.clean()
        route.routing_table = self.table
        with self.assertRaises(ValidationError):
            route.clean()

    def test_source_and_next_hop_interfaces_must_be_local(self):
        from nautobot.dcim.models import Interface

        remote = Interface.objects.create(
            device=self.other_device, name="Ethernet1", type="1000base-t", status=self.active
        )
        for values in ({"next_hop": remote}, {"source_interface": remote}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                self.route(**values).clean()
        self.route(next_hop=self.interface).clean()

    def test_ipv4_ipv6_mismatch(self):
        prefix = Prefix.objects.create(prefix="2001:db8::/64", namespace=self.namespace, status=self.active)
        prefix.vrfs.add(self.vrf)
        for hop in (self.ip, self.transit):
            with self.assertRaises(ValidationError):
                self.route(prefix=prefix, next_hop=hop).clean()

    def test_unsupported_and_dangling_next_hop(self):
        with self.assertRaises(ValidationError):
            self.route(next_hop=self.device).clean()
        with self.assertRaises(ValidationError):
            self.route(next_hop_type=ContentType.objects.get_for_model(self.ip), next_hop_id=uuid4()).clean()
        with self.assertRaises(ValidationError):
            self.route(next_hop_id=uuid4()).clean()

    def test_default_route_accepts_gateway(self):
        prefix = Prefix.objects.create(prefix="0.0.0.0/0", namespace=self.namespace, status=self.active)
        prefix.vrfs.add(self.vrf)
        self.route(prefix=prefix, next_hop=self.ip).validated_save()

    def test_duplicate_routes_without_next_hop_are_rejected(self):
        self.route().validated_save()
        with self.assertRaises(ValidationError):
            self.route().validated_save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.route().save()

    def test_managed_queryset_and_distance_range(self):
        route = self.route(is_managed=True, source_interface=self.interface, protocol="connected")
        route.validated_save()
        self.assertEqual(list(Route.managed_connected_qs()), [route])
        for distance in (-1, 256):
            with self.assertRaises(ValidationError):
                self.route(admin_distance=distance).full_clean()
