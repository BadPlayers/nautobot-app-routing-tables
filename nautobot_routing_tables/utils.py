from nautobot.apps.config import get_app_settings_or_config


def get_setting(name: str, fallback):
    return get_app_settings_or_config("nautobot_routing_tables", name, fallback=fallback)
