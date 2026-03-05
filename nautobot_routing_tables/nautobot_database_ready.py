from django.db.models.signals import post_migrate
from django.dispatch import receiver

from nautobot.apps import nautobot_database_ready

from .seed import ensure_default_protocol_types
from .signals import register_signals


@nautobot_database_ready.connect
def on_db_ready(sender, **kwargs):
    register_signals()


@receiver(post_migrate)
def _post_migrate_seed(sender, **kwargs):
    try:
        ensure_default_protocol_types()
    except Exception:
        pass
