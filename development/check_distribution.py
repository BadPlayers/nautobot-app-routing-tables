"""Fail a release build if its compiled documentation is missing."""

from pathlib import Path
from zipfile import ZipFile


wheels = list(Path("dist").glob("*.whl"))
if not wheels:
    raise SystemExit("No wheel found in dist/")
for wheel in wheels:
    with ZipFile(wheel) as archive:
        names = set(archive.namelist())
        root = "nautobot_routing_tables/static/nautobot_routing_tables/docs/"
        for page in ("index.html", "user/ui.html", "admin/release_notes/version_1.2.html"):
            if root + page not in names:
                raise SystemExit(f"{wheel}: missing documentation page {page}")
        if not any(name.startswith(root + "assets/") for name in names):
            raise SystemExit(f"{wheel}: missing documentation assets")
        print(f"{wheel}: compiled documentation and assets verified")
