from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

menu_items = (
    NavMenuTab(
        name="Routing",
        groups=(
            NavMenuGroup(
                name="Routing Tables",
                items=(
                    NavMenuItem(
                        link="plugins:nautobot_routing_tables:routingtable_list",
                        name="Routing Tables",
                        buttons=(
                            NavMenuAddButton(
                                link="plugins:nautobot_routing_tables:routingtable_add"
                            ),
                        ),
                    ),
                    NavMenuItem(
                        link="plugins:nautobot_routing_tables:routingprotocol_list",
                        name="Routing Protocol Overrides",
                        buttons=(
                            NavMenuAddButton(
                                link="plugins:nautobot_routing_tables:routingprotocol_add"
                            ),
                        ),
                    ),
                    NavMenuItem(
                        link="plugins:nautobot_routing_tables:route_list",
                        name="Routes",
                        buttons=(
                            NavMenuAddButton(
                                link="plugins:nautobot_routing_tables:route_add"
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
)