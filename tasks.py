try:
    from invoke import task
except Exception:
    task = None  # type: ignore

if task:
    @task
    def docs(c):
        c.run("mkdocs build")
        c.run("python -m nautobot_routing_tables.tools.copy_docs_to_static")
