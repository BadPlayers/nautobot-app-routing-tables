from __future__ import annotations

import shutil
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parents[2]
    site_dir = repo_root / "site"
    if not site_dir.exists():
        raise SystemExit("MkDocs site directory not found. Run `mkdocs build` first.")
    static_docs = repo_root / "nautobot_routing_tables" / "static" / "nautobot_routing_tables" / "docs"
    if static_docs.exists():
        shutil.rmtree(static_docs)
    static_docs.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(site_dir, static_docs)
    print(f"Copied docs from {site_dir} to {static_docs}")


if __name__ == "__main__":
    main()
