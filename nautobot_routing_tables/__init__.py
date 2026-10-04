"""App declaration for nautobot_routing_tables."""

from importlib import metadata

from nautobot.apps import NautobotAppConfig

try:
    __version__ = metadata.version("nautobot-app-routing-tables")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"


class NautobotRoutingTablesConfig(NautobotAppConfig):
    """App configuration for the nautobot_routing_tables app."""

    name = "nautobot_routing_tables"
    verbose_name = "Nautobot Routing Tables"
    version = __version__
    author = "Never77"
    description = "Nautobot Routing Tables."
    base_url = "routing-tables"
    min_version = "2.4.0"
    max_version = "3.9999"
    required_settings = []
    default_settings = {
        "AUTO_MANAGE_CONNECTED_ROUTES": True,
        "AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES": True,
        "REQUIRE_CABLE_FOR_CONNECTED_ROUTES": True,
    }
    searchable_models = []

    home_view_name = "plugins:nautobot_routing_tables:routingtable_list"
    config_view_name = "plugins:nautobot_routing_tables:config"

    def ready(self):
        """Register receivers in web and worker processes alike."""
        super().ready()
        from . import signals

        signals.register_signals()


config = NautobotRoutingTablesConfig
