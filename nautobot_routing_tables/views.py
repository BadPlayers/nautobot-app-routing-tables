"""Routing UI views and the table-to-routes creation workflow."""

from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView
from django_tables2 import RequestConfig
from nautobot.apps.ui import LayoutChoices, ObjectDetailContent, Panel, SectionChoices
from nautobot.apps.views import NautobotUIViewSet
from nautobot.ipam.filters import IPAddressFilterSet, PrefixFilterSet
from nautobot.ipam.models import Prefix

from .api.serializers import RouteSerializer, RoutingProtocolSerializer, RoutingTableSerializer
from .choices import choice_label, routing_choices
from .filters import RouteFilterSet, RoutingProtocolFilterSet, RoutingTableFilterSet
from .forms import (
    RouteBulkEditForm,
    RouteForm,
    RoutingProtocolBulkEditForm,
    RoutingProtocolForm,
    RoutingTableBulkEditForm,
    RoutingTableForm,
)
from .models import Route, RoutingProtocol, RoutingTable
from .services import export_routing_tables_as_csv, optimized_routes
from .tables import (
    RouteTable,
    RoutingProtocolTable,
    RoutingTableDetailProtocolTable,
    RoutingTableDetailRouteTable,
    RoutingTableTable,
)


class ConfigView(TemplateView):
    """Display application configuration help."""

    template_name = "nautobot_routing_tables/config.html"


class RoutingTableUIViewSet(NautobotUIViewSet):
    """Manage routing tables and show their permitted child routes."""

    queryset = RoutingTable.objects.select_related("device", "vrf")
    serializer_class = RoutingTableSerializer
    filterset_class = RoutingTableFilterSet
    table_class = RoutingTableTable
    form_class = RoutingTableForm
    bulk_update_form_class = RoutingTableBulkEditForm

    def get_queryset(self):
        """Count only routes visible to this user in the table overview."""
        return (
            super()
            .get_queryset()
            .annotate(
                route_count=Count("routes", filter=Q(routes__in=Route.objects.restrict(self.request.user, "view")))
            )
        )

    def _process_create_or_update_form(self, form):
        creating = not form.instance.present_in_database
        super()._process_create_or_update_form(form)
        if (
            creating
            and form.cleaned_data.get("add_routes")
            and self.request.user.has_perm("nautobot_routing_tables.add_route")
        ):
            self.success_url = f"{reverse('plugins:nautobot_routing_tables:route_add')}?{urlencode({'routing_table': form.instance.pk})}"

    object_detail_content = ObjectDetailContent(
        layout=LayoutChoices.ONE_OVER_TWO,
        panels=[
            Panel(
                label="Protocol preferences",
                section=SectionChoices.FULL_WIDTH,
                weight=300,
                body_content_template_path="nautobot_routing_tables/inc/protocol_preferences.html",
            ),
            Panel(
                label="Routes",
                section=SectionChoices.FULL_WIDTH,
                weight=200,
                body_content_template_path="nautobot_routing_tables/inc/routingtable_routes_panel.html",
                header_extra_content_template_path="nautobot_routing_tables/inc/routingtable_routes_panel_header.html",
            ),
        ],
    )

    def get_extra_context(self, request, instance=None):
        """Build the permitted route table and creation link."""
        context = super().get_extra_context(request, instance=instance)

        if instance is not None:
            routes = optimized_routes(
                Route.objects.restrict(request.user, "view").filter(routing_table=instance)
            ).order_by("prefix__prefix_length", "prefix__network")

            routes_table = RoutingTableDetailRouteTable(routes, user=request.user)
            RequestConfig(request, paginate={"per_page": 25}).configure(routes_table)

            context["routes_table"] = routes_table
            context["routes_count"] = routes.count()
            context["add_routes_url"] = reverse(
                "plugins:nautobot_routing_tables:routingtable_add_routes", kwargs={"pk": instance.pk}
            )
            context["export_routes_url"] = reverse(
                "plugins:nautobot_routing_tables:routingtable_export", kwargs={"pk": instance.pk}
            )
            context["protocols_table"] = RoutingTableDetailProtocolTable(
                RoutingProtocol.objects.restrict(request.user, "view")
                .filter(routing_table=instance)
                .select_related("routing_table__device", "routing_table__vrf"),
                user=request.user,
            )
            context["add_protocol_url"] = (
                f"{reverse('plugins:nautobot_routing_tables:routingprotocol_add')}?routing_table={instance.pk}"
            )
            context["add_route_url"] = (
                f"{reverse('plugins:nautobot_routing_tables:route_add')}?routing_table={instance.pk}"
            )

        return context


@login_required
def route_choices(request):
    """Serve paginated, permission-filtered choices for dependent form widgets."""
    if not request.GET.get("routing_table"):
        return JsonResponse({"count": 0, "results": [], "next": None, "previous": None})
    try:
        table = get_object_or_404(
            RoutingTable.objects.restrict(request.user, "view"), pk=request.GET.get("routing_table")
        )
        destination = (
            Prefix.objects.restrict(request.user, "view").filter(pk=request.GET["prefix"]).first()
            if request.GET.get("prefix")
            else None
        )
        offset = max(0, int(request.GET.get("offset", 0)))
    except (ValueError, ValidationError):
        return JsonResponse({"count": 0, "results": [], "next": None, "previous": None})
    kind = request.GET.get("kind", "ip")
    if kind not in {"ip", "prefix", "interface"}:
        return JsonResponse({"error": "Unknown next-hop type"}, status=400)
    choices = routing_choices(kind, table, destination).restrict(request.user, "view")
    query = request.GET.get("q", "").strip()
    if query:
        if kind == "interface":
            choices = choices.filter(name__icontains=query)
        else:
            filter_class = PrefixFilterSet if kind == "prefix" else IPAddressFilterSet
            choices = filter_class({"q": query}, queryset=choices).qs
    count = choices.count()
    results = [
        {"id": str(obj.pk), "display": choice_label(obj)} for obj in choices.order_by("pk")[offset : offset + 50]
    ]
    return JsonResponse(
        {
            "count": count,
            "results": results,
            "next": "more" if count > offset + 50 else None,
            "previous": None if offset == 0 else "previous",
        }
    )


@login_required
def export_table(request, pk):
    """Download visible routes directly from a permitted table."""
    table = get_object_or_404(RoutingTable.objects.restrict(request.user, "view"), pk=pk)
    routes = Route.objects.restrict(request.user, "view").filter(routing_table=table)
    response = HttpResponse(
        export_routing_tables_as_csv(routes, RoutingProtocol.objects.restrict(request.user, "view")),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="routes-{table.pk}.csv"'
    return response


class RoutingProtocolUIViewSet(NautobotUIViewSet):
    """Manage protocol overrides within their routing table."""

    queryset = RoutingProtocol.objects.select_related("routing_table__device", "routing_table__vrf")
    serializer_class = RoutingProtocolSerializer
    filterset_class = RoutingProtocolFilterSet
    table_class = RoutingProtocolTable
    form_class = RoutingProtocolForm
    bulk_update_form_class = RoutingProtocolBulkEditForm

    def get_form_kwargs(self):
        """Initialize the parent table without overriding submitted data."""
        kwargs = super().get_form_kwargs()
        if not kwargs.get("data") and self.request.GET.get("routing_table"):
            kwargs.setdefault("initial", {})
            kwargs["initial"]["routing_table"] = self.request.GET["routing_table"]
        return kwargs


class RouteUIViewSet(NautobotUIViewSet):
    """Manage routes while retaining their parent table during entry."""

    queryset = optimized_routes(Route.objects.all())
    serializer_class = RouteSerializer
    filterset_class = RouteFilterSet
    table_class = RouteTable
    form_class = RouteForm
    bulk_update_form_class = RouteBulkEditForm

    def _process_create_or_update_form(self, form):
        super()._process_create_or_update_form(form)
        if "_addanother" in self.request.POST:
            query = urlencode({"routing_table": form.instance.routing_table_id, "protocol": form.instance.protocol})
            self.success_url = f"{reverse('plugins:nautobot_routing_tables:route_add')}?{query}"
        elif not form.cleaned_data.get("return_url"):
            self.success_url = form.instance.routing_table.get_absolute_url()

    def get_form_kwargs(self):
        """Initialize the parent table without overriding submitted data."""
        kwargs = super().get_form_kwargs()
        if not kwargs.get("data") and self.request.GET.get("routing_table"):
            kwargs.setdefault("initial", {})
            kwargs["initial"]["routing_table"] = self.request.GET["routing_table"]
        return kwargs
