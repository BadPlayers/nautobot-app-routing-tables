"""Exercise real signal delivery, including m2m bulk operations and deletion."""

from unittest.mock import patch

from django.db import transaction
from nautobot.dcim.models import Interface
from nautobot.ipam.models import IPAddressToInterface

from nautobot_routing_tables import signals
from nautobot_routing_tables.models import Route
from nautobot_routing_tables.services import reconcile_connected_routes_for_interface
from nautobot_routing_tables.tests.base import RoutingTestCase


class SignalsTestCase(RoutingTestCase):
    def setUp(self):
        self.settings_patch = patch(
            "nautobot_routing_tables.services.get_setting",
            side_effect=lambda name, fallback: name != "REQUIRE_CABLE_FOR_CONNECTED_ROUTES",
        )
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)

    def test_interface_disable_and_enable(self):
        reconcile_connected_routes_for_interface(self.interface)
        with self.captureOnCommitCallbacks(execute=True):
            self.interface.enabled = False
            self.interface.save()
        self.assertFalse(Route.objects.exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.interface.enabled = True
            self.interface.save()
        self.assertEqual(Route.objects.count(), 1)

    def test_m2m_remove_add_and_clear(self):
        reconcile_connected_routes_for_interface(self.interface)
        with self.captureOnCommitCallbacks(execute=True):
            self.interface.ip_addresses.remove(self.ip)
        self.assertFalse(Route.objects.exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.interface.ip_addresses.add(self.ip)
        self.assertEqual(Route.objects.count(), 1)
        with self.captureOnCommitCallbacks(execute=True):
            self.ip.interfaces.clear()
        self.assertFalse(Route.objects.exists())

    def test_direct_assignment_delete(self):
        reconcile_connected_routes_for_interface(self.interface)
        with self.captureOnCommitCallbacks(execute=True):
            IPAddressToInterface.objects.get(interface=self.interface, ip_address=self.ip).delete()
        self.assertFalse(Route.objects.exists())

    def test_direct_assignment_move_cleans_old_interface(self):
        other = Interface.objects.create(
            device=self.device, name="Ethernet2", type="1000base-t", status=self.active, vrf=self.vrf
        )
        reconcile_connected_routes_for_interface(self.interface)
        assignment = IPAddressToInterface.objects.get(interface=self.interface, ip_address=self.ip)
        with self.captureOnCommitCallbacks(execute=True):
            assignment.interface = other
            assignment.save()
        self.assertEqual(Route.objects.get().source_interface, other)

    def test_ip_deleted_removes_managed_routes(self):
        reconcile_connected_routes_for_interface(self.interface)
        with self.captureOnCommitCallbacks(execute=True):
            self.ip.delete()
        self.assertFalse(Route.objects.exists())

    def test_interface_deleted_does_not_leave_orphan_managed_routes(self):
        reconcile_connected_routes_for_interface(self.interface)
        with self.captureOnCommitCallbacks(execute=True):
            self.interface.delete()
        self.assertFalse(Route.objects.exists())

    def test_ip_mask_change_replaces_network(self):
        reconcile_connected_routes_for_interface(self.interface)
        with self.captureOnCommitCallbacks(execute=True):
            self.ip.mask_length = 25
            self.ip.save()
        self.assertEqual(str(Route.objects.get().prefix.prefix), "192.0.2.0/25")

    def test_fixture_save_and_rollback_do_not_reconcile(self):
        with patch("nautobot_routing_tables.signals.reconcile_connected_routes_for_interface") as reconcile:
            signals.interface_saved(Interface, self.interface, raw=True)
            with self.captureOnCommitCallbacks(execute=True):
                try:
                    with transaction.atomic():
                        self.interface.save()
                        raise ValueError("rollback")
                except ValueError:
                    pass
            reconcile.assert_not_called()

    def test_disabled_setting_register_and_database_ready(self):
        from nautobot_routing_tables import nautobot_database_ready

        self.assertIsNone(signals.register_signals())
        nautobot_database_ready.on_db_ready(sender=None)
        nautobot_database_ready._post_migrate_seed(sender=None)
        with (
            patch("nautobot_routing_tables.signals.connected_routes_enabled", return_value=False),
            self.captureOnCommitCallbacks(execute=True) as callbacks,
        ):
            signals.interface_saved(Interface, self.interface)
        self.assertEqual(callbacks, [])

    def test_cable_removal_reconciles_former_endpoints(self):
        from nautobot.dcim.models import Cable
        from nautobot.extras.models import Status

        other = Interface.objects.create(
            device=self.other_device, name="Ethernet2", type="1000base-t", status=self.active
        )
        # Enable the cable requirement for this case.
        self.settings_patch.stop()
        with patch("nautobot_routing_tables.services.get_setting", return_value=True):
            with self.captureOnCommitCallbacks(execute=True):
                cable = Cable.objects.create(
                    termination_a=self.interface, termination_b=other, status=Status.objects.get(name="Connected")
                )
            self.assertEqual(Route.objects.count(), 1)
            from nautobot_routing_tables.services import reconcile_connected_routes_for_cable

            reconcile_connected_routes_for_cable(cable)
            with self.captureOnCommitCallbacks(execute=True):
                cable.delete()
            self.assertFalse(Route.objects.exists())

    def test_table_creation_reconciles_existing_addresses(self):
        from nautobot_routing_tables.models import RoutingTable

        self.table.delete()
        with self.captureOnCommitCallbacks(execute=True):
            table = RoutingTable.objects.create(device=self.device, vrf=self.vrf)
        self.assertEqual(Route.objects.get().routing_table, table)

    def test_reverse_m2m_add_remove(self):
        self.interface.ip_addresses.clear()
        with self.captureOnCommitCallbacks(execute=True):
            self.ip.interfaces.add(self.interface)
        self.assertEqual(Route.objects.count(), 1)
        with self.captureOnCommitCallbacks(execute=True):
            self.ip.interfaces.remove(self.interface)
        self.assertFalse(Route.objects.exists())
