from nautobot.apps.jobs import FileVar, Job, ObjectVar, register_jobs

from .models import Route, RoutingTable
from .services import (
    CSV_TEMPLATE_HEADER,
    export_routing_tables_as_csv,
    import_routing_tables_from_csv,
    reconcile_connected_routes_for_all_devices,
)


class ReconcileConnectedRoutesAllDevices(Job):
    class Meta:
        name = "Reconcile Connected Routes (All Devices)"
        description = "Rebuild managed connected routes from current interface/IP/cable state."

    def run(self, **kwargs):
        reconcile_connected_routes_for_all_devices()
        return "Reconciled connected routes for all interfaces."


class ImportRoutingTablesCSV(Job):
    class Meta:
        name = "Import Routing Tables from CSV"
        description = "Create routing tables, routes and protocol overrides from a single CSV file."

    input_file = FileVar(description="CSV file matching the routing tables import template.")

    def run(self, *, input_file):
        stats = import_routing_tables_from_csv(input_file.read())
        return f"Imported {stats['routing_tables']} routing tables, {stats['routes']} routes and {stats['overrides']} overrides."


class ExportRoutingTablesCSV(Job):
    class Meta:
        name = "Export Routing Tables to CSV"
        description = "Export routes and protocol overrides to a flat CSV file."

    routing_table = ObjectVar(model=RoutingTable, required=False, description="Optional routing table filter.")

    def run(self, *, routing_table=None):
        queryset = Route.objects.all()
        if routing_table is not None:
            queryset = queryset.filter(routing_table=routing_table)
        self.create_file("routing_tables_export.csv", export_routing_tables_as_csv(queryset))
        return f"Exported {queryset.count()} routes."


class DownloadRoutingTablesCSVTemplate(Job):
    class Meta:
        name = "Download Routing Tables CSV Template"
        description = "Generate a CSV template for one-shot routing table imports."

    def run(self):
        self.create_file("routing_tables_import_template.csv", CSV_TEMPLATE_HEADER)
        return "Generated CSV template."


register_jobs(
    ReconcileConnectedRoutesAllDevices,
    ImportRoutingTablesCSV,
    ExportRoutingTablesCSV,
    DownloadRoutingTablesCSVTemplate,
)

jobs = [
    ReconcileConnectedRoutesAllDevices,
    ImportRoutingTablesCSV,
    ExportRoutingTablesCSV,
    DownloadRoutingTablesCSVTemplate,
]
