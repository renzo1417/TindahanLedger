import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.home.forms import BusinessSettingsForm
from apps.home.models import CustomerLedgerTransaction, ProductBatch, SalesTransactionItem
from apps.home.services import current_store, preferences, lock_store


@login_required
def user_settings_view(request):
    store = request.store = current_store(request.user)
    form = BusinessSettingsForm(request.POST or None, instance=preferences(store))
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            lock_store(store)
            form.save()
        messages.success(request, 'Business settings saved.')
        return redirect('user_settings:index')
    return render(request, 'user_settings/user_settings.html', {'active_nav': 'settings', 'form': form})


@login_required
@require_POST
def reset_view(request):
    store = current_store(request.user)
    with transaction.atomic():
        lock_store(store)
        settings = preferences(store)
        for name in BusinessSettingsForm.Meta.fields:
            setattr(settings, name, settings._meta.get_field(name).get_default())
        settings.save()
    messages.success(request, 'Business defaults restored. Existing customer limits and product thresholds are unchanged.')
    return redirect('user_settings:index')


def csv_cell(value):
    text = str(value or '')
    return "'"+text if text.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else text


@login_required
def export_csv_view(request):
    store = current_store(request.user)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="customers-{timezone.localdate()}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Nickname', 'Phone', 'Balance', 'Credit limit', 'Due date'])
    for c in store.customers.order_by('name'):
        writer.writerow([c.pk, csv_cell(c.name), csv_cell(c.nickname), csv_cell(c.phone), str(c.running_balance), str(c.credit_limit), c.due_date or ''])
    return response


@login_required
def export_json_view(request):
    store = current_store(request.user)
    def records(queryset, excluded=()):
        fields = [f.name for f in queryset.model._meta.fields if f.name not in excluded]
        return list(queryset.values(*fields))
    payload = {
        'format_version': 1, 'exported_at': timezone.now(),
        'store': records(type(store).objects.filter(pk=store.pk), ('user', 'is_device_synced'))[0],
        'settings': {name: getattr(preferences(store), name) for name in BusinessSettingsForm.Meta.fields},
        'customers': records(store.customers.all()), 'categories': records(store.categories.all()),
        'products': records(store.products.all()), 'batches': records(ProductBatch.objects.filter(product__store=store)),
        'ledger_entries': records(CustomerLedgerTransaction.objects.filter(customer__store=store)),
        'sales': records(store.sales_transactions.all()),
        'sale_items': records(SalesTransactionItem.objects.filter(transaction__store=store)),
        'reminder_simulations': records(store.sms_reminders.filter(sent_status='simulated')),
    }
    response = JsonResponse(payload, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="ledger-{timezone.localdate()}.json"'
    return response
