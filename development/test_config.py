"""Isolated configuration shared by local and CI tests."""
import os
from importlib.metadata import version

from nautobot.core.settings import *  # noqa: F403

SECRET_KEY = "routing-tables-disposable-test-environment"  # noqa: S105
ALLOWED_HOSTS = ["*"]
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "nautobot", "USER": "nautobot", "PASSWORD": "testing",
    "HOST": os.getenv("NAUTOBOT_DB_HOST", "routing-tables-test-db"), "PORT": "5432",
    "TEST": {"NAME": os.getenv("ROUTING_TEST_DATABASE", "test_routing_tables24")},
}}
CACHES = {"default": {"BACKEND": "django_redis.cache.RedisCache", "KEY_PREFIX": "routing-tests-" + version("nautobot"), "LOCATION": os.getenv("NAUTOBOT_REDIS_URL", "redis://routing-tables-test-redis:6379/1")}}
PLUGINS = ["nautobot_routing_tables"]
PLUGINS_CONFIG = {"nautobot_routing_tables": {"AUTO_MANAGE_CONNECTED_ROUTES": False}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
