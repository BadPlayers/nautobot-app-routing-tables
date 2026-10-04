from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from nautobot_routing_tables import jobs, seed, utils


class RuntimeHelpersTestCase(SimpleTestCase):
    @patch("nautobot_routing_tables.utils.get_app_settings_or_config")
    def test_get_setting_delegates_to_nautobot_helper(self, get_config):
        get_config.return_value = "value"
        self.assertEqual(utils.get_setting("FOO", "bar"), "value")
        get_config.assert_called_once_with("nautobot_routing_tables", "FOO", fallback="bar")

    def test_seed_defaults_is_noop(self):
        self.assertIsNone(seed.seed_defaults())


class JobsTestCase(SimpleTestCase):
    @patch("nautobot_routing_tables.jobs.reconcile_connected_routes_for_all_devices")
    def test_reconcile_job_runs_service(self, reconcile):
        job = jobs.ReconcileConnectedRoutesAllDevices()
        self.assertEqual(job.run(), "Reconciled connected routes for all interfaces.")
        reconcile.assert_called_once_with()

    @patch("nautobot_routing_tables.jobs.import_routing_tables_from_csv")
    def test_import_job_returns_summary(self, importer):
        importer.return_value = {"routing_tables": 1, "routes": 2, "overrides": 3}
        job = jobs.ImportRoutingTablesCSV()
        payload = SimpleNamespace(read=Mock(return_value=b"csv"))
        self.assertEqual(
            job.run(input_file=payload),
            "Imported 1 routing tables, 2 routes and 3 overrides.",
        )

    @patch("nautobot_routing_tables.jobs.export_routing_tables_as_csv", return_value="csv-data")
    @patch("nautobot_routing_tables.jobs.Route.objects")
    def test_export_job_creates_file(self, route_objects, export_csv):
        queryset = Mock()
        filtered_queryset = Mock()
        filtered_queryset.count.return_value = 4
        queryset.filter.return_value = filtered_queryset
        route_objects.all.return_value = queryset
        job = jobs.ExportRoutingTablesCSV()
        job.create_file = Mock()
        routing_table = SimpleNamespace()

        message = job.run(routing_table=routing_table)

        queryset.filter.assert_called_once_with(routing_table=routing_table)
        job.create_file.assert_called_once_with("routing_tables_export.csv", "csv-data")
        self.assertEqual(message, "Exported 4 routes.")

    def test_template_job_creates_template_file(self):
        job = jobs.DownloadRoutingTablesCSVTemplate()
        job.create_file = Mock()

        message = job.run()

        job.create_file.assert_called_once_with("routing_tables_import_template.csv", jobs.CSV_TEMPLATE_HEADER)
        self.assertEqual(message, "Generated CSV template.")
