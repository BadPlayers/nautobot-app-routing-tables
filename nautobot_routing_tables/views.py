from django.views.generic import TemplateView
from nautobot.apps.views import NautobotUIViewSet

from .filters import ProtocolTypeFilterSet, RouteFilterSet, RoutingProtocolFilterSet, RoutingTableFilterSet
from .forms import ProtocolTypeForm, RouteForm, RoutingProtocolForm, RoutingTableForm
from .models import ProtocolType, Route, RoutingProtocol, RoutingTable
from .tables import ProtocolTypeTable, RouteTable, RoutingProtocolTable, RoutingTableTable


class ConfigView(TemplateView):
    template_name = "nautobot_routing_tables/config.html"


class ProtocolTypeUIViewSet(NautobotUIViewSet):
    queryset = ProtocolType.objects.all()
    filterset_class = ProtocolTypeFilterSet
    table_class = ProtocolTypeTable
    form_class = ProtocolTypeForm


class RoutingTableUIViewSet(NautobotUIViewSet):
    queryset = RoutingTable.objects.select_related("device", "vrf")
    filterset_class = RoutingTableFilterSet
    table_class = RoutingTableTable
    form_class = RoutingTableForm


class RoutingProtocolUIViewSet(NautobotUIViewSet):
    queryset = RoutingProtocol.objects.select_related("routing_table", "protocol_type")
    filterset_class = RoutingProtocolFilterSet
    table_class = RoutingProtocolTable
    form_class = RoutingProtocolForm


class RouteUIViewSet(NautobotUIViewSet):
    queryset = Route.objects.select_related("routing_table", "prefix", "protocol", "next_hop_interface", "source_interface")
    filterset_class = RouteFilterSet
    table_class = RouteTable
    form_class = RouteForm
