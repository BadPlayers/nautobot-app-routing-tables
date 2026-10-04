"""Run historical migrations with actual legacy records in an isolated schema."""

from importlib import import_module

from django.db import connection
from django.db.migrations.loader import MigrationLoader

from nautobot_routing_tables.tests.base import RoutingTestCase


class LegacyMigrationTestCase(RoutingTestCase):
    def test_upgrade_preserves_legacy_routes_and_allows_new_inserts(self):
        loader = MigrationLoader(connection)
        state = loader.project_state(("nautobot_routing_tables", "0001_initial"))
        app = "nautobot_routing_tables"
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA routing_migration_test")
            cursor.execute("SET LOCAL search_path TO routing_migration_test, public")
        try:
            models = {
                name: state.apps.get_model(app, name)
                for name in ("ProtocolType", "RoutingTable", "RoutingProtocol", "Route")
            }
            with connection.schema_editor() as editor:
                for model in models.values():
                    editor.create_model(model)
            protocol_type = models["ProtocolType"].objects.create(
                name="Static", slug="static", default_admin_distance=1
            )
            table = models["RoutingTable"].objects.create(
                name="Old table", slug="old-table", device_id=self.device.pk, vrf_id=self.vrf.pk
            )
            protocol = models["RoutingProtocol"].objects.create(
                name="Custom static name",
                slug="custom-static-name",
                routing_table=table,
                protocol_type=protocol_type,
                parameters={"tag": 7},
            )
            interface_route = models["Route"].objects.create(
                routing_table=table,
                prefix_id=self.prefix.pk,
                protocol=protocol,
                next_hop_interface_id=self.interface.pk,
            )
            ip_route = models["Route"].objects.create(
                routing_table=table, prefix_id=self.transit.pk, protocol=protocol, next_hop_ip="192.0.2.1"
            )
            # PostgreSQL must finish deferred FK checks before table alteration.
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            for name in (
                "0002_routing_table_cleanup",
                "0003_alter_routingprotocol_options_and_more",
                "0004_repair_legacy_schema",
                "0005_route_unique_route_without_next_hop",
            ):
                migration = import_module(f"{app}.migrations.{name}").Migration(name, app)
                with connection.schema_editor() as editor:
                    state = migration.apply(state, editor)
            upgraded = state.apps.get_model(app, "Route")
            self.assertEqual(upgraded.objects.get(pk=interface_route.pk).next_hop_id, self.interface.pk)
            self.assertEqual(upgraded.objects.get(pk=ip_route.pk).next_hop_id, self.ip.pk)
            self.assertEqual(upgraded.objects.get(pk=ip_route.pk).protocol, "static")
            preference = state.apps.get_model(app, "RoutingProtocol").objects.get(pk=protocol.pk)
            self.assertEqual(preference.admin_distance_override, 1)
            self.assertEqual(preference.parameters, {"tag": 7})
            state.apps.get_model(app, "RoutingTable").objects.create(device_id=self.other_device.pk)
            state.apps.get_model(app, "RoutingProtocol").objects.create(
                routing_table_id=table.pk, protocol="ospf", admin_distance_override=110
            )
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL search_path TO public")
                cursor.execute("DROP SCHEMA routing_migration_test CASCADE")

    def test_repair_shipped_integer_column_without_discarding_values(self):
        repair = import_module("nautobot_routing_tables.migrations.0004_repair_legacy_schema").repair_schema
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA routing_migration_test")
            cursor.execute("SET LOCAL search_path TO routing_migration_test, public")
            cursor.execute("CREATE TABLE nautobot_routing_tables_route (next_hop_id bigint)")
            cursor.execute("CREATE TABLE nautobot_routing_tables_routingtable (name text NOT NULL, slug text NOT NULL)")
            cursor.execute(
                "CREATE TABLE nautobot_routing_tables_routingprotocol (name text NOT NULL, slug text NOT NULL, protocol_type_id uuid NOT NULL)"
            )
            cursor.execute("INSERT INTO nautobot_routing_tables_route VALUES (123)")
        try:
            with connection.schema_editor() as editor:
                with self.assertRaisesRegex(RuntimeError, "manual repair"):
                    repair(None, editor)
            with connection.cursor() as cursor:
                cursor.execute("SELECT next_hop_id FROM nautobot_routing_tables_route")
                self.assertEqual(cursor.fetchone()[0], 123)
                cursor.execute("DELETE FROM nautobot_routing_tables_route")
            with connection.schema_editor() as editor:
                repair(None, editor)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT data_type FROM information_schema.columns WHERE table_schema = 'routing_migration_test' AND table_name = 'nautobot_routing_tables_route' AND column_name = 'next_hop_id'"
                )
                self.assertEqual(cursor.fetchone()[0], "uuid")
                cursor.execute("INSERT INTO nautobot_routing_tables_routingtable DEFAULT VALUES")
                cursor.execute("INSERT INTO nautobot_routing_tables_routingprotocol DEFAULT VALUES")
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL search_path TO public")
                cursor.execute("DROP SCHEMA routing_migration_test CASCADE")
