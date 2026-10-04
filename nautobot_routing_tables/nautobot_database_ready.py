"""Database-ready and migration initialization hooks."""

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from nautobot.apps import nautobot_database_ready

from .seed import seed_defaults
from .signals import register_signals


@receiver(nautobot_database_ready)
def on_db_ready(sender, **kwargs):
    """Ensure signal receivers have been registered."""
    register_signals()


@receiver(post_migrate)
def _post_migrate_seed(sender, **kwargs):
    seed_defaults()
