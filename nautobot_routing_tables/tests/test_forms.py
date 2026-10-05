"""Form validation uses real UUID next-hops before any database write."""

from nautobot_routing_tables.forms import RouteForm, RoutingTableForm
from nautobot_routing_tables.models import Route, RoutingProtocol, RoutingTable
from nautobot_routing_tables.tests.base import RoutingTestCase


class RouteFormTestCase(RoutingTestCase):
    def data(self, **kwargs):
        data = {
            "routing_table": self.table.pk,
            "prefix": self.prefix.pk,
            "protocol": "static",
            "next_hop": "192.0.2.1",
            "metric": 0,
        }
        data.update(kwargs)
        return data

    def test_form_validates_and_saves_uuid_next_hop(self):
        form = RouteForm(data=self.data())
        self.assertTrue(form.is_valid(), form.errors)
        route = form.save()
        self.assertEqual(route.next_hop, self.ip)
        self.assertEqual(route.metric, 0)

    def test_form_unknown_next_hop_returns_field_error(self):
        form = RouteForm(data=self.data(next_hop="missing"))
        self.assertFalse(form.is_valid())
        self.assertIn("next_hop", form.errors)

    def test_form_missing_required_fields_does_not_crash(self):
        form = RouteForm(data={"next_hop": "192.0.2.1"})
        self.assertFalse(form.is_valid())
        self.assertIn("routing_table", form.errors)

    def test_form_clear_next_hop(self):
        route = Route.objects.create(routing_table=self.table, prefix=self.prefix, protocol="static", next_hop=self.ip)
        form = RouteForm(instance=route, data=self.data(next_hop=""))
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        route.refresh_from_db()
        self.assertIsNone(route.next_hop_id)
        self.assertIsNone(route.next_hop_type_id)

    def test_form_initial_typed_next_hop_and_static_default(self):
        route = Route.objects.create(routing_table=self.table, prefix=self.prefix, protocol="static", next_hop=self.ip)
        form = RouteForm(instance=route)
        self.assertEqual(form.initial["next_hop_kind"], "ip")
        self.assertEqual(form.initial["next_hop_object"], str(self.ip.pk))
        self.assertIn("192.0.2.1", str(form["next_hop_object"]))
        self.assertEqual(RouteForm().initial["protocol"], "static")

    def test_table_form_offers_add_routes_only_when_creating(self):
        self.assertTrue(RoutingTableForm().fields["add_routes"].initial)
        self.assertNotIn("add_routes", RoutingTableForm(instance=self.table).fields)

    def test_bulk_forms_use_real_querysets(self):
        from nautobot_routing_tables.forms import (
            RouteBulkEditForm,
            RoutingProtocolBulkEditForm,
            RoutingTableBulkEditForm,
        )

        self.assertIn(self.vrf, RoutingTableBulkEditForm(model=RoutingTable).fields["vrf"].queryset)
        self.assertIn(self.table, RoutingTableBulkEditForm(model=RoutingTable).fields["pk"].queryset)
        self.assertIsNotNone(RouteBulkEditForm(model=Route).fields["pk"].queryset)
        self.assertIsNotNone(RoutingProtocolBulkEditForm(model=RoutingProtocol).fields["pk"].queryset)

    def test_model_next_hop_errors_map_to_form_field(self):
        from nautobot.ipam.models import Prefix

        prefix = Prefix.objects.create(prefix="2001:db8::/64", namespace=self.namespace, status=self.active)
        prefix.vrfs.add(self.vrf)
        form = RouteForm(data=self.data(prefix=prefix.pk))
        self.assertFalse(form.is_valid())
        self.assertIn("next_hop", form.errors)
