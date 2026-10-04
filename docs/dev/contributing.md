# Contributing

Create a branch from `main` and open a pull request against `main`. Include a clear
description, relevant regression tests and release-note updates. The repository
does not require a separate develop branch.

Run the checks in [Testing](testing.md). CI requires lint, migration consistency,
the supported Nautobot matrix and at least 95% branch-aware application coverage.
Do not replace ORM regression tests with mocks for database relationship changes.

Use [the release checklist](release_checklist.md) for publication. Documentation is
built with MkDocs; keep the user guides and compatibility table aligned with code.
