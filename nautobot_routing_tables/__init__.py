"""App declaration for nautobot_routing_tables."""

from importlib import metadata

from nautobot.apps import NautobotAppConfig

try:
    __version__ = metadata.version(__name__)
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
    required_settings = []
    default_settings = {}
    searchable_models = []

    home_view_name = "plugins:nautobot_routing_tables:routingtable_list"
    config_view_name = "plugins:nautobot_routing_tables:config"

config = NautobotRoutingTablesConfig