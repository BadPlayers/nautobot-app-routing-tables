from nautobot.apps import NautobotAppConfig


class NautobotRoutingTablesConfig(NautobotAppConfig):
    name = "nautobot_routing_tables"
    verbose_name = "Routing Tables"
    description = "Model routing tables per device and VRF, including optional auto-managed connected routes."
    version = "1.1.0"
    author = "Your Name"
    author_email = "you@example.com"
    base_url = "routing-tables"
    min_version = "2.4.0"
    max_version = "4.0.0"

    config_view_name = "plugins:nautobot_routing_tables:config"
    menu_items = "nautobot_routing_tables.navigation.menu_items"


config = NautobotRoutingTablesConfig
