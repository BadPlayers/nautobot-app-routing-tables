from django.test import SimpleTestCase

from nautobot_routing_tables.api import serializers, urls, views


class RoutingAPITestCase(SimpleTestCase):
    def test_api_router_registered_prefixes(self):
        self.assertEqual(
            [prefix for prefix, _, _ in urls.router.registry],
            ["routing-tables", "routing-protocols", "routes"],
        )

    def test_route_serializer_exposes_computed_fields(self):
        self.assertIn("next_hop_display", serializers.RouteSerializer._declared_fields)
        self.assertIn("resolved_admin_distance", serializers.RouteSerializer._declared_fields)
