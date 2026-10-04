# Testing

Use Python 3.12 and PostgreSQL plus Redis in an isolated development environment.
CI installs each of Nautobot 2.4.0, 2.4.26, 3.0.0 and 3.2.6 and runs the same suite.

```shell
python -m pip install 'nautobot==2.4.26' coverage 'ruff==0.5.5' build
python -m pip install --no-deps -e .
export NAUTOBOT_CONFIG="$PWD/development/test_config.py"
export NAUTOBOT_DB_HOST=localhost
export NAUTOBOT_REDIS_URL=redis://localhost:6379/1
nautobot-server makemigrations nautobot_routing_tables --check --dry-run
ruff check nautobot_routing_tables
coverage run -m nautobot.core.cli test nautobot_routing_tables.tests --noinput
coverage report --fail-under=95
python -m build
```

`test_config.py` is only for disposable test services. Its PostgreSQL database,
user and password are `nautobot`, `nautobot` and `testing`. The user must be able
to create test databases. Never use this configuration for a deployed service.
Set `ROUTING_TEST_DATABASE` to a different name for each Nautobot version when
sharing a PostgreSQL server. Do not reuse a database upgraded to Nautobot 3.x
with a Nautobot 2.4 process.

The suite includes isolated unit tests and real ORM, signal, CSV, REST, UI,
permission, query-count and migration regression tests. The upgrade tests create
legacy tables in a temporary schema and verify UUID gateway preservation,
protocol preferences and new inserts after migration. The integer-column repair
also verifies that inconsistent old values are rejected without being erased.

Coverage includes application and documentation-helper Python modules and
branches. It excludes tests and migration source; migrations are verified by the
explicit regression cases and fresh database creation rather than coverage
percentage. SQL export tests ensure that query counts stay constant as route
counts increase within a batch.
