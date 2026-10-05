"""Regression tests for contextual route entry and atomic batch creation."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.urls import reverse
from nautobot.dcim.models import Interface
from nautobot.ipam.models import Prefix
from nautobot.users.models import ObjectPermission

from nautobot_routing_tables.forms import RouteForm
from nautobot_routing_tables.models import Route, RoutingProtocol
from nautobot_routing_tables.tables import RouteTable
from nautobot_routing_tables.tests.base import RoutingTestCase


class RoutingUXTestCase(RoutingTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(username="ux-admin", password="testing")
        self.client.force_login(self.user)
        self.batch_url = reverse(
            "plugins:nautobot_routing_tables:routingtable_add_routes", kwargs={"pk": self.table.pk}
        )
        self.choices_url = reverse("plugins:nautobot_routing_tables:route_choices")

    def row(self, **kwargs):
        data = {
            "routing_table": str(self.table.pk),
            "prefix": str(self.prefix.pk),
            "protocol": "static",
            "next_hop_kind": "ip",
            "next_hop_object": str(self.ip.pk),
        }
        data.update(kwargs)
        return data

    def batch_data(self, *rows):
        data = {
            "form-TOTAL_FORMS": str(len(rows)),
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "1",
            "form-MAX_NUM_FORMS": "50",
        }
        for index, row in enumerate(rows):
            data.update({f"form-{index}-{key}": value for key, value in row.items()})
        return data

    def test_table_list_has_direct_link_and_permitted_count(self):
        Route.objects.create(routing_table=self.table, prefix=self.prefix, protocol="static")
        response = self.client.get(reverse("plugins:nautobot_routing_tables:routingtable_list"), HTTP_HX_REQUEST="true")
        self.assertContains(response, f'href="{self.table.get_absolute_url()}"')
        self.assertContains(response, "Add route")

    def test_next_hop_selector_saves_and_rejects_other_device(self):
        form = RouteForm(data=self.row())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().next_hop, self.ip)
        other = Interface.objects.create(device=self.other_device, name="Wrong", type="1000base-t", status=self.active)
        form = RouteForm(data=self.row(next_hop_kind="interface", next_hop_object=str(other.pk)))
        self.assertFalse(form.is_valid())
        self.assertIn("next_hop_object", form.errors)

    def test_interface_selector_and_conflicting_text(self):
        form = RouteForm(data=self.row(next_hop_kind="interface", next_hop_object=str(self.interface.pk)))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().next_hop, self.interface)
        form = RouteForm(data=self.row(next_hop="192.0.2.1"))
        self.assertFalse(form.is_valid())
        self.assertIn("next_hop", form.errors)

    def test_choices_scope_search_and_family(self):
        data = {"routing_table": self.table.pk, "kind": "ip", "prefix": self.prefix.pk, "q": "192.0.2.1"}
        response = self.client.get(self.choices_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["id"], str(self.ip.pk))
        self.assertIn(self.namespace.name, response.json()["results"][0]["display"])
        prefix6 = Prefix.objects.create(prefix="2001:db8::/64", namespace=self.namespace, status=self.active)
        prefix6.vrfs.add(self.vrf)
        data["prefix"] = prefix6.pk
        self.assertEqual(self.client.get(self.choices_url, data).json()["results"], [])
        form = RouteForm(data=self.row(prefix=str(prefix6.pk)))
        self.assertFalse(form.is_valid())
        self.assertIn("next_hop_object", form.errors)

    def test_empty_and_invalid_choices_do_not_error(self):
        for params in ({}, {"routing_table": "invalid"}, {"routing_table": self.table.pk, "offset": "invalid"}):
            self.assertEqual(self.client.get(self.choices_url, params).json()["results"], [])
        self.assertEqual(
            self.client.get(self.choices_url, {"routing_table": self.table.pk, "kind": "bad"}).status_code, 400
        )

    def test_choices_require_table_permission(self):
        user = get_user_model().objects.create_user(username="no-routing-permission")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.choices_url, {"routing_table": self.table.pk}).status_code, 404)
        self.assertEqual(self.client.get(self.batch_url).status_code, 403)

    def test_batch_page_and_table_actions_render(self):
        self.assertContains(self.client.get(self.batch_url), "Save all routes")
        response = self.client.get(self.table.get_absolute_url())
        self.assertContains(response, self.batch_url)
        self.assertContains(response, "Add protocol override")
        self.assertContains(response, "Export CSV")

    def test_batch_saves_multiple_routes_and_skips_blank_rows(self):
        response = self.client.post(
            self.batch_url,
            self.batch_data(self.row(), self.row(prefix=str(self.transit.pk)), self.row(prefix="", next_hop_object="")),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Route.objects.count(), 2)

    def test_batch_invalid_or_duplicate_row_saves_nothing(self):
        for row in (self.row(next_hop_object="not-a-uuid"), self.row()):
            response = self.client.post(self.batch_url, self.batch_data(self.row(), row))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Route.objects.count(), 0)

    def test_batch_rejects_parent_tampering(self):
        response = self.client.post(self.batch_url, self.batch_data(self.row(routing_table=str(self.global_table.pk))))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Route.objects.count(), 0)

    def test_batch_add_and_duplicate_preserve_inputs_without_saving(self):
        data = self.batch_data(self.row())
        data["_more"] = ""
        response = self.client.post(self.batch_url, data)
        self.assertEqual(response.context["formset"].total_form_count(), 6)
        data.pop("_more")
        data["_duplicate"] = "0"
        response = self.client.post(self.batch_url, data)
        self.assertEqual(response.context["formset"].forms[1]["prefix"].value(), str(self.prefix.pk))
        self.assertEqual(Route.objects.count(), 0)

    def test_export_and_distance_provenance(self):
        route = Route.objects.create(routing_table=self.table, prefix=self.prefix, protocol="static")
        table = RouteTable([route], user=self.user)
        self.assertIn("Protocol default", table.render_admin_distance(route))
        RoutingProtocol.objects.create(routing_table=self.table, protocol="static", admin_distance_override=5)
        self.assertIn("Table override", table.render_admin_distance(route))
        response = self.client.get(
            reverse("plugins:nautobot_routing_tables:routingtable_export", kwargs={"pk": self.table.pk})
        )
        self.assertContains(response, "10.10.0.0/24")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_batch_database_failure_rolls_back_first_row(self):
        from nautobot_routing_tables.forms import BatchRouteForm

        save = BatchRouteForm.save
        calls = []

        def fail_second(form, *args, **kwargs):
            calls.append(form)
            if len(calls) == 2:
                raise IntegrityError("Concurrent duplicate")
            return save(form, *args, **kwargs)

        with patch.object(BatchRouteForm, "save", fail_second):
            response = self.client.post(
                self.batch_url, self.batch_data(self.row(), self.row(prefix=str(self.transit.pk)))
            )
        self.assertContains(response, "No routes were saved")
        self.assertEqual(Route.objects.count(), 0)

    def test_export_respects_override_permissions(self):
        from nautobot_routing_tables.models import RoutingTable

        Route.objects.create(routing_table=self.table, prefix=self.prefix, protocol="static")
        RoutingProtocol.objects.create(
            routing_table=self.table,
            protocol="static",
            admin_distance_override=5,
            parameters={"private": "hidden-setting"},
        )
        user = get_user_model().objects.create_user(username="route-reader")
        permission = ObjectPermission.objects.create(name="Read routes and tables", actions=["view"])
        permission.object_types.add(
            ContentType.objects.get_for_model(Route), ContentType.objects.get_for_model(RoutingTable)
        )
        permission.users.add(user)
        self.client.force_login(user)
        response = self.client.get(
            reverse("plugins:nautobot_routing_tables:routingtable_export", kwargs={"pk": self.table.pk})
        )
        self.assertContains(response, "10.10.0.0/24")
        self.assertNotContains(response, "hidden-setting")

    def test_get_form_keeps_requested_protocol(self):
        response = self.client.get(
            reverse("plugins:nautobot_routing_tables:route_add"), {"routing_table": self.table.pk, "protocol": "ospf"}
        )
        self.assertContains(response, 'value="ospf" selected')

    def test_batch_ignores_empty_first_row_and_rejects_empty_batch(self):
        empty = self.row(prefix="", next_hop_object="")
        response = self.client.post(self.batch_url, self.batch_data(empty))
        self.assertContains(response, "Enter at least one route")
        response = self.client.post(self.batch_url, self.batch_data(empty, self.row()))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Route.objects.count(), 1)

    def test_batch_limits_size_and_handles_invalid_management(self):
        data = self.batch_data(self.row())
        data["form-TOTAL_FORMS"] = "99999"
        response = self.client.post(self.batch_url, data)
        self.assertEqual(len(response.context["formset"].forms), 50)
        self.assertEqual(Route.objects.count(), 0)
        data["form-TOTAL_FORMS"] = "invalid"
        data["_more"] = ""
        self.assertEqual(self.client.post(self.batch_url, data).status_code, 200)

    def test_batch_add_constraints_roll_back_all_rows(self):
        from nautobot.ipam.models import IPAddress

        from nautobot_routing_tables.models import RoutingTable

        user = get_user_model().objects.create_user(username="static-route-editor")
        permission = ObjectPermission.objects.create(name="Read routing context", actions=["view"])
        permission.object_types.add(
            *(ContentType.objects.get_for_model(model) for model in (RoutingTable, Prefix, IPAddress))
        )
        permission.users.add(user)
        permission = ObjectPermission.objects.create(
            name="Create only static routes", actions=["add"], constraints={"protocol": "static"}
        )
        permission.object_types.add(ContentType.objects.get_for_model(Route))
        permission.users.add(user)
        self.client.force_login(user)
        response = self.client.post(
            self.batch_url, self.batch_data(self.row(), self.row(prefix=str(self.transit.pk), protocol="ospf"))
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Route.objects.count(), 0)
