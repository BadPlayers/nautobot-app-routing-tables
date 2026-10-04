# Release Checklist

1. Update `pyproject.toml`, the Docker requirements reference and the release notes.
2. Run lint, migration checks, the PostgreSQL test matrix and distribution builds
   as described in [Testing](testing.md).
3. Open a pull request against `main` and wait for every CI matrix job to pass.
4. Merge the reviewed changes, then create a version tag on that exact commit.
5. Publish a GitHub release with the detailed notes from `docs/admin/release_notes/`.
6. Verify **Upload Python Package** passes its test dependency and PyPI trusted
   publishing job, and verify the version on PyPI.
7. Verify **Build Docker Image** publishes the tagged source to GHCR.

The repository uses GitHub releases to trigger PyPI publication. It has no
Prepare Release workflow or required `develop` branch. Publishing credentials
are managed through GitHub's `pypi` environment and trusted publishing; do not
add registry tokens to the repository.
