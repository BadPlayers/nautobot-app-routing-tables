from django.test import SimpleTestCase

from nautobot_routing_tables import jobs


class RoutingJobsTestCase(SimpleTestCase):
    def test_csv_jobs_are_registered(self):
        job_names = [job.__name__ for job in jobs.jobs]
        self.assertIn("ImportRoutingTablesCSV", job_names)
        self.assertIn("ExportRoutingTablesCSV", job_names)
        self.assertIn("DownloadRoutingTablesCSVTemplate", job_names)
