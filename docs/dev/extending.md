# Extending the App

Keep protocol constants in `constants.py`, shared business logic in `services.py`
and data validation in `models.py`. UI and CSV next-hop resolution must use the
same resolver. Preserve object permissions when adding detail panels.

Use Django migrations for schema changes. Retain compatibility with Nautobot 2.4
and 3.x, and add a regression test reproducing the changed behavior. See
[Testing](testing.md) and [Signals](signals.md).
