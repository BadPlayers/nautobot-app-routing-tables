# Development Environment

## Docker development environment

The repository includes Compose services for Nautobot, its workers, PostgreSQL,
Redis and a MkDocs documentation server. Copy `invoke.example.yml` to
`invoke.yml` and `development/creds.example.env` to `development/creds.env`, then
set the local database credentials. Keep credentials outside version control.

Install Poetry and Docker, install the development dependencies and use the
Invoke tasks in `tasks.py`. The default development image is Nautobot 3.0.0 with
Python 3.12; set `nautobot_ver` to select another supported version. Use the
PostgreSQL Compose configuration; the old MySQL template does not provide support
for the app's historical PostgreSQL migrations.

## Documentation server

Install the documentation dependencies and serve the current source:

```shell
python -m pip install -r development/docs-requirements.txt
mkdocs serve --dev-addr 127.0.0.1:8001
```

The Compose `docs` service exposes this documentation on port 8001 and mounts the
repository, so source changes are reflected by live reload. The navigation
includes the UI/CSV workflow, connected routes, configuration, permissions,
compatibility, upgrade guide, release notes and developer testing instructions.

## Embedded documentation

Build and copy the same site into the app's static assets:

```shell
mkdocs build --strict
python nautobot_routing_tables/tools/copy_docs_to_static.py
python -m build
```

The build uses explicit `.html` links so the pages also work under Nautobot's
static-file server. The app configuration page links to the packaged documentation.
After installation, `nautobot-server post_upgrade` collects those assets for your
Nautobot static server. PyPI and Docker release builds perform the site-generation
steps automatically; generated assets are not source-controlled.

## Tests

See [Testing](testing.md) for the isolated PostgreSQL/Redis configuration and the
four-version compatibility matrix. Application tests do not require a running
web server or a production database.
