ARG NAUTOBOT_IMAGE=networktocode/nautobot:3.2.6-py3.12
FROM python:3.12-slim AS docs
WORKDIR /source
COPY . .
RUN pip install -r development/docs-requirements.txt && \
    mkdocs build --strict && \
    python nautobot_routing_tables/tools/copy_docs_to_static.py

FROM ${NAUTOBOT_IMAGE}
# Install the exact tagged source, including its compiled documentation.
COPY --from=docs --chown=nautobot:nautobot /source /tmp/routing-tables
RUN pip install --no-deps /tmp/routing-tables && rm -rf /tmp/routing-tables
