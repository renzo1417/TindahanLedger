from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from apps.home.forms import CustomerForm, LedgerForm
from apps.home.models import Customer
from apps.home.selectors import customers_for, customer_status, sms_message
from apps.home.services import current_store, preferences, create_customer, record_entry


@login_required
def customer_list_view(request):
    store = request.store = current_store(request.user)
    customers = customers_for(store)
    selected = request.GET.get('filter', 'all')
    query = request.GET.get('q', '').strip()
    filtered = [c for c in customers if (selected == 'all' or c.status == selected or selected == 'owing' and c.running_balance > 0) and
                (not query or query.casefold() in f'{c.name} {c.nickname} {c.phone}'.casefold())]
    return render(request, 'customers/customer_list.html', {'active_nav': 'utang', 'customers': filtered,
        'selected_filter': selected, 'search_query': query, 'total_balance': sum(c.running_balance for c in customers),
        'customer_count': len(customers), 'owing_count': sum(c.running_balance > 0 for c in customers),
        'overdue_count': sum(c.status == 'overdue' for c in customers)})


@login_required
def customer_detail_view(request, customer_id):
    store = request.store = current_store(request.user)
    customer = get_object_or_404(Customer, pk=customer_id, store=store)
    if request.method == 'POST':
        return _save_entry(request, store, customer_id)
    customer_status(customer, preferences(store).overdue_grace_days)
    return render(request, 'customers/customer_detail.html', {'active_nav': 'utang', 'customer': customer,
        'transactions': customer.ledger_transactions.order_by('-transaction_date', '-pk'),
        'form': LedgerForm(initial={'customer_id': customer.pk, 'kind': 'utang', 'payment_mode': 'Cash'}),
        'sms_preview': sms_message(customer, store)})


@login_required
def customer_create_view(request):
    store = request.store = current_store(request.user)
    form = CustomerForm(request.POST or None, initial={'credit_limit': preferences(store).default_credit_limit})
    if request.method == 'POST' and form.is_valid():
        try:
            customer = create_customer(store, form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Customer added to your ledger.')
            return redirect('customers:customer_detail', customer_id=customer.pk)
    return render(request, 'customers/customer_create.html', {'active_nav': 'utang', 'form': form})


def _save_entry(request, store, customer_id=None):
    data = request.POST.copy()
    data['customer_id'] = customer_id or data.get('customer_id', '')
    data['kind'] = data.get('kind') or data.get('action_type', '')
    data['summary'] = data.get('summary') or data.get('items_summary', '')
    form = LedgerForm(data)
    if form.is_valid():
        cleaned = dict(form.cleaned_data)
        customer_id = cleaned.pop('customer_id')
        try:
            record_entry(store, customer_id, **cleaned)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Payment recorded.' if cleaned['kind'] == 'bayad' else 'Debt adjustment recorded. This is not a product sale.')
            return redirect('customers:customer_detail', customer_id=customer_id)
    candidate = customer_id or data.get('customer_id', '')
    customer = get_object_or_404(Customer, store=store, pk=candidate) if str(candidate).isdigit() else None
    return render(request, 'customers/entry_form.html', {'active_nav': 'utang', 'form': form, 'customer': customer,
        'customers': store.customers.order_by('name')}, status=400)


@login_required
@require_POST
def entry_view(request):
    return _save_entry(request, current_store(request.user))


@login_required
def entry_form_view(request):
    store = request.store = current_store(request.user)
    kind = 'bayad' if request.GET.get('kind') == 'bayad' else 'utang'
    customer_id = request.GET.get('customer', '')
    customer = get_object_or_404(Customer, store=store, pk=customer_id) if customer_id.isdigit() else None
    return render(request, 'customers/entry_form.html', {'active_nav': 'utang', 'form': LedgerForm(initial={'kind': kind, 'customer_id': customer.pk if customer else None}),
        'customer': customer, 'customers': store.customers.order_by('name')})
