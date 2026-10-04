"""Build-helper tests use temporary directories, never the repository assets."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from nautobot_routing_tables.tools import copy_docs_to_static


class PackagedDocsTestCase(SimpleTestCase):
    def test_missing_site_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(copy_docs_to_static, "__file__", str(Path(root) / "app/tools/copy.py")):
                with self.assertRaisesRegex(SystemExit, "MkDocs"):
                    copy_docs_to_static.main()

    def test_copy_replaces_previous_docs(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            site = root / "site"
            site.mkdir()
            (site / "index.html").write_text("First build")
            with (
                patch.object(copy_docs_to_static, "__file__", str(root / "app/tools/copy.py")),
                patch("builtins.print"),
            ):
                copy_docs_to_static.main()
                (site / "index.html").write_text("Second build")
                copy_docs_to_static.main()
            target = root / "nautobot_routing_tables/static/nautobot_routing_tables/docs/index.html"
            self.assertEqual(target.read_text(), "Second build")
