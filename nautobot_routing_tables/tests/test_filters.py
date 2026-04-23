from django.test import SimpleTestCase

from nautobot_routing_tables import filters


class RoutingFilterTestCase(SimpleTestCase):
    def test_routing_protocol_filterset_fields(self):
        self.assertEqual(
            filters.RoutingProtocolFilterSet.Meta.fields,
            ["routing_table", "protocol", "admin_distance_override"],
        )

    def test_route_filterset_fields(self):
        self.assertEqual(
            filters.RouteFilterSet.Meta.fields,
            ["routing_table", "prefix", "protocol", "is_managed"],
        )
