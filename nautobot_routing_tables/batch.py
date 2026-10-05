"""Atomic multi-route entry from a routing table."""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BatchRouteForm
from .models import Route, RoutingTable


class RouteBatchFormSet(forms.BaseFormSet):
    """Detect duplicate forwarding decisions before saving any row."""

    def clean(self):
        """Report duplicates on the row that repeats an earlier route."""
        super().clean()
        seen = set()
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE") or form.errors:
                continue
            route = form.instance
            key = (route.prefix_id, route.protocol, route.next_hop_type_id, route.next_hop_id)
            if key in seen:
                form.add_error("prefix", "This route duplicates an earlier row.")
            seen.add(key)
        if not seen and not any(form.errors for form in self.forms if not form.cleaned_data.get("DELETE")):
            raise forms.ValidationError("Enter at least one route before saving.")


RouteBatch = forms.formset_factory(
    BatchRouteForm,
    formset=RouteBatchFormSet,
    extra=5,
    max_num=50,
    absolute_max=50,
    validate_max=True,
    can_delete=True,
)


@login_required
@permission_required("nautobot_routing_tables.add_route", raise_exception=True)
def add_routes(request, pk):
    """Validate a batch, then save all permitted rows in one transaction."""
    table = get_object_or_404(
        RoutingTable.objects.restrict(request.user, "view").select_related("device", "vrf"), pk=pk
    )
    data = request.POST.copy() if request.method == "POST" else None
    editing_rows = data is not None and ("_more" in data or "_duplicate" in data)
    if editing_rows:
        try:
            total = min(50, max(0, int(data.get("form-TOTAL_FORMS", 0))))
            if "_duplicate" in data:
                index = int(data["_duplicate"])
                if 0 <= index < total < 50:
                    for key in list(data):
                        if key.startswith(f"form-{index}-") and not key.endswith("-DELETE"):
                            data[key.replace(f"form-{index}-", f"form-{total}-", 1)] = data[key]
                    total += 1
            else:
                total = min(50, total + 5)
            data["form-TOTAL_FORMS"] = str(total)
        except ValueError:
            pass  # The formset will report invalid management data on Save.
    formset = RouteBatch(data=data, form_kwargs={"table": table})
    for form in formset:
        form.fields["DELETE"].label = "Skip this row"
        for name in ("routing_table", "prefix", "next_hop_object"):
            form.fields[name].queryset = form.fields[name].queryset.restrict(request.user, "view")
    error = None
    if request.method == "POST" and not editing_rows and formset.is_valid():
        try:
            with transaction.atomic():
                count = 0
                for form in formset:
                    if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                        continue
                    route = form.save()
                    if not Route.objects.restrict(request.user, "add").filter(pk=route.pk).exists():
                        raise PermissionDenied
                    count += 1
            messages.success(request, f"Created {count} routes in {table}.")
            return redirect(table.get_absolute_url())
        except (IntegrityError, ValidationError):
            error = "No routes were saved. A route may already exist or the routing context changed. Check the rows and retry."
    return render(
        request, "nautobot_routing_tables/route_batch.html", {"table": table, "formset": formset, "batch_error": error}
    )
