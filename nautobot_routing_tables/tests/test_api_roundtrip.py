"""REST round-trips verify serializer validation, UUIDs and filtering."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from nautobot_routing_tables.models import Route
from nautobot_routing_tables.tests.base import RoutingTestCase


class RoutingAPIRoundTripTestCase(RoutingTestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            get_user_model().objects.create_superuser(username="api-admin", password="test-password")
        )
        self.url = reverse("plugins-api:nautobot_routing_tables-api:route-list")

    def payload(self, **kwargs):
        data = {
            "routing_table": str(self.table.pk),
            "prefix": str(self.prefix.pk),
            "protocol": "static",
            "next_hop_type": "ipam.ipaddress",
            "next_hop_id": str(self.ip.pk),
        }
        data.update(kwargs)
        return data

    def test_create_route_with_uuid_next_hop(self):
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(Route.objects.get().next_hop, self.ip)
        self.assertEqual(response.json()["resolved_admin_distance"], 1)

    def test_reject_invalid_next_hop_and_mismatched_family(self):
        for fields in (
            {"next_hop_id": "00000000-0000-0000-0000-000000000001"},
            {"next_hop_id": None},
            {"admin_distance": 999},
        ):
            response = self.client.post(self.url, self.payload(**fields), format="json")
            self.assertEqual(response.status_code, 400, response.json())
        self.assertFalse(Route.objects.exists())

    def test_api_filtering_and_clear_next_hop(self):
        route = Route.objects.create(routing_table=self.table, prefix=self.prefix, protocol="static", next_hop=self.ip)
        Route.objects.create(routing_table=self.table, prefix=self.transit, protocol="ospf")
        response = self.client.get(self.url, {"protocol": "static"})
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["count"], 1)
        detail_url = reverse("plugins-api:nautobot_routing_tables-api:route-detail", kwargs={"pk": route.pk})
        response = self.client.patch(detail_url, {"next_hop_id": None, "next_hop_type": None}, format="json")
        self.assertEqual(response.status_code, 200, response.json())
        route.refresh_from_db()
        self.assertIsNone(route.next_hop)
