"""Exercise UI creation workflows and object-level route visibility."""

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from django.urls import reverse
from nautobot.users.models import ObjectPermission

from nautobot_routing_tables import tables, views
from nautobot_routing_tables.models import Route, RoutingTable
from nautobot_routing_tables.tests.base import RoutingTestCase


class RoutingUIWorkflowTestCase(RoutingTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(username="routing-admin", password="test-password")
        self.client.force_login(self.user)

    def test_create_table_opens_first_route_form(self):
        response = self.client.post(
            reverse("plugins:nautobot_routing_tables:routingtable_add"),
            {
                "device": self.other_device.pk,
                "vrf": self.vrf.pk,
                "add_routes": "on",
            },
        )
        self.assertEqual(response.status_code, 302, getattr(response, "context_data", None))
        table = RoutingTable.objects.get(device=self.other_device, vrf=self.vrf)
        parsed = urlsplit(response.url)
        self.assertEqual(parsed.path, reverse("plugins:nautobot_routing_tables:route_add"))
        self.assertEqual(parse_qs(parsed.query)["routing_table"], [str(table.pk)])

    def test_create_route_add_another_preserves_selected_table_and_protocol(self):
        response = self.client.post(
            reverse("plugins:nautobot_routing_tables:route_add"),
            {
                "routing_table": self.table.pk,
                "prefix": self.prefix.pk,
                "protocol": "ospf",
                "_addanother": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlsplit(response.url).query)
        self.assertEqual(query["routing_table"], [str(self.table.pk)])
        self.assertEqual(query["protocol"], ["ospf"])
        self.assertEqual(Route.objects.count(), 1)

    def test_save_route_returns_to_parent_table(self):
        response = self.client.post(
            reverse("plugins:nautobot_routing_tables:route_add"),
            {
                "routing_table": self.table.pk,
                "prefix": self.prefix.pk,
                "protocol": "static",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.table.get_absolute_url())

    def test_detail_page_and_add_form_render(self):
        Route.objects.create(routing_table=self.table, prefix=self.prefix, protocol="static", next_hop=self.ip)
        response = self.client.get(self.table.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "192.0.2.1")
        response = self.client.get(
            reverse("plugins:nautobot_routing_tables:route_add"), {"routing_table": self.table.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.table.pk))

    def test_child_routes_respect_object_permissions(self):
        visible = Route.objects.create(routing_table=self.table, prefix=self.prefix, protocol="ospf")
        Route.objects.create(routing_table=self.table, prefix=self.transit, protocol="static")
        user = get_user_model().objects.create_user(username="limited")
        permission = ObjectPermission.objects.create(
            name="One route", actions=["view"], constraints={"pk": str(visible.pk)}
        )
        permission.object_types.add(ContentType.objects.get_for_model(Route))
        permission.users.add(user)
        request = RequestFactory().get("/")
        request.user = user
        view = views.RoutingTableUIViewSet()
        with patch.object(views.NautobotUIViewSet, "get_extra_context", return_value={}):
            context = view.get_extra_context(request, self.table)
        self.assertEqual(context["routes_count"], 1)

    def test_action_buttons_and_distance_renderers(self):
        route = Route.objects.create(routing_table=self.table, prefix=self.prefix, protocol="static", admin_distance=0)
        for table_class in (tables.RouteTable, tables.RoutingTableDetailRouteTable):
            table = table_class([route], user=self.user)
            self.assertIn("0 <small", table.render_admin_distance(route))
            self.assertIn("Route override", table.render_admin_distance(route))
            html = tables.RouteActionsColumn().render(route, table)
            self.assertIn("Edit", html)
            self.assertIn("Delete", html)
        user = get_user_model().objects.create_user(username="no-permissions")
        table = tables.RouteTable([route], user=user)
        self.assertEqual(str(tables.RouteActionsColumn().render(route, table)), "")

    def test_parent_initial_values(self):
        for cls in (views.RouteUIViewSet, views.RoutingProtocolUIViewSet):
            view = cls()
            view.request = RequestFactory().get("/", {"routing_table": self.table.pk})
            with patch.object(views.NautobotUIViewSet, "get_form_kwargs", return_value={}):
                self.assertEqual(view.get_form_kwargs()["initial"]["routing_table"], str(self.table.pk))
            with patch.object(
                views.NautobotUIViewSet, "get_form_kwargs", return_value={"data": {"protocol": "static"}}
            ):
                self.assertNotIn("initial", view.get_form_kwargs())
