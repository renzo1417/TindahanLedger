"""Public product story with private, store-scoped previews after sign-in."""
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from apps.home.views import overview_context
from apps.home.services import ZERO
from apps.home.models import CustomerLedgerTransaction, SalesTransaction
from apps.home.selectors import batches_for, financial_report, period_start
from apps.home.services import current_store


def landing_view(request):
    order = 'arrival' if request.GET.get('order') == 'arrival' else 'expiry'
    context = {'stock_order': order}
    if request.user.is_authenticated:
        store = current_store(request.user)
        summary, _ = financial_report(store)
        customer = store.customers.order_by('-running_balance', 'name').first()
        batches = [b for b in batches_for(store) if b.quantity > 0 and not b.disposed_at]
        if order == 'arrival':
            batches.sort(key=lambda batch: (batch.created_at, batch.pk))
        context = {
            'stock_order': order,
            'preview_store': store, 'preview_summary': summary, 'preview_customer': customer,
            'preview_entries': CustomerLedgerTransaction.objects.filter(customer=customer).order_by('-transaction_date')[:3] if customer else [],
            'preview_batches': batches[:6],
            'preview_sales': SalesTransaction.objects.filter(store=store, transaction_date__gte=period_start('today')).select_related('customer').order_by('-transaction_date')[:3],
            'preview_payment': CustomerLedgerTransaction.objects.filter(customer__store=store, transaction_type='bayad').order_by('-transaction_date').first(),
            'preview_activity': overview_context(store)['activity'][:3],
            'preview_featured': next((b for b in batches if b.display_status in ('expiring_soon', 'healthy')), None),
            'preview_expired': next((b for b in batches if b.display_status == 'expired'), None),
        }
        context['preview_other_batches'] = [b for b in batches if b != context['preview_featured'] and b.display_status == 'healthy'][:2]
    return render(request, 'landing/landing.html', context)


@xframe_options_sameorigin
def dashboard_preview(request):
    """Show the current dashboard design without exposing anyone else's records."""
    if request.user.is_authenticated:
        store = request.store = current_store(request.user)
        context = overview_context(store)
    else:
        context = {
            'active_nav': 'home',
            'summary': dict.fromkeys(('cash_collected', 'cash_sales', 'payments_received', 'uncollected_utang', 'gross_sales', 'gross_profit', 'transactions_count'), ZERO),
            'global_store_profile': {'store_name': 'Your tindahan', 'owner_name': '', 'current_date_display': timezone.localdate().strftime('%d %b %Y')},
            'global_store_kpis': {'overdue_accounts_count': 0},
            'urgent_batches': [], 'overdue_customers': [], 'activity': [],
        }
        context['summary']['transactions_count'] = 0
    return render(request, 'home/home.html', context)
