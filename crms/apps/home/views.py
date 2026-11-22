from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from .models import SalesTransaction, CustomerLedgerTransaction
from .selectors import customers_for, batches_for, financial_report, period_start
from .services import current_store


@login_required
def home_view(request):
    store = request.store = current_store(request.user)
    return render(request, 'home/home.html', overview_context(store))


def overview_context(store):
    """Shared, read-only data for the dashboard and its landing-page preview."""
    summary, _ = financial_report(store)
    customers = customers_for(store)
    urgent = [b for b in batches_for(store) if b.quantity > 0 and b.display_status in ('expired', 'expiring_soon', 'missing_date')]
    sales = list(SalesTransaction.objects.filter(store=store, transaction_date__gte=period_start('today')).select_related('customer').order_by('-transaction_date')[:15])
    payments = list(CustomerLedgerTransaction.objects.filter(customer__store=store, transaction_type='bayad', transaction_date__gte=period_start('today')).select_related('customer').order_by('-transaction_date')[:15])
    activity = sorted([{'date': s.transaction_date, 'label': s.customer.name if s.customer else 'Walk-in customer',
                        'kind': s.payment_method+' sale', 'summary': s.items_summary, 'amount': s.total_amount} for s in sales] +
                      [{'date': p.transaction_date, 'label': p.customer.name, 'kind': 'Payment received',
                        'summary': p.payment_mode, 'amount': p.amount} for p in payments], key=lambda x: x['date'], reverse=True)[:15]
    return {'active_nav': 'home', 'summary': summary,
        'urgent_batches': urgent[:5], 'overdue_customers': [c for c in customers if c.status == 'overdue'][:5], 'activity': activity}


@login_required
def search_view(request):
    store = current_store(request.user)
    query = request.GET.get('q', '').strip()[:100]
    results = []
    if query:
        for c in store.customers.filter(Q(name__icontains=query) | Q(nickname__icontains=query) | Q(phone__icontains=query)).order_by('name')[:10]:
            results.append({'label': c.name, 'detail': f'Customer · ₱{c.running_balance:,.2f}', 'url': reverse('customers:customer_detail', args=[c.pk])})
        for p in store.products.filter(Q(name__icontains=query) | Q(sku__icontains=query)).order_by('name')[:10]:
            results.append({'label': p.name, 'detail': f'Product · {p.stock_quantity} {p.unit}', 'url': reverse('inventory:product_detail', args=[p.pk])})
    return JsonResponse({'results': results})
