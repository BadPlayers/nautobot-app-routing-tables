from nautobot.apps.jobs import Job

from .services import connected_routes_enabled, reconcile_connected_routes_for_all_devices


class ReconcileConnectedRoutesAllDevices(Job):
    class Meta:
        name = "Reconcile Connected Routes (All Devices)"
        description = "Rebuild managed connected routes from current interface/IP/cable state."

    def run(self, **kwargs):
        if not connected_routes_enabled():
            return "AUTO_MANAGE_CONNECTED_ROUTES is disabled; no changes were made."
        reconcile_connected_routes_for_all_devices()
        return "Reconciled connected routes for all interfaces."


jobs = [ReconcileConnectedRoutesAllDevices]
