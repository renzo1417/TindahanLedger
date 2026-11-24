"""Public product story with illustrative Figma previews and private, store-scoped previews after sign-in."""
from datetime import datetime, time
from decimal import Decimal
from types import SimpleNamespace

from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin

from apps.home.models import CustomerLedgerTransaction, SalesTransaction
from apps.home.selectors import batches_for, financial_report, period_start
from apps.home.services import current_store
from apps.home.views import overview_context


def _sample_time(hour, minute):
    today = timezone.localdate()
    return timezone.make_aware(datetime.combine(today, time(hour, minute)))


def _public_landing_preview(order):
    """Illustrative in-memory sample matching the Figma showcase (0 DB queries)."""
    sellable_batches = [
        SimpleNamespace(
            product=SimpleNamespace(name='Pancit Canton', unit='packs'),
            batch_code='BT-2026-081',
            shelf_location='Estante A-1',
            quantity=12,
            days_left=3,
            display_status='expiring_soon',
            display_label='3 araw pa',
            arrival_order=3,
            action_hint='Ilipat sa harap ng estante',
        ),
        SimpleNamespace(
            product=SimpleNamespace(name='Pancit Canton', unit='packs'),
            batch_code='BT-2026-095',
            shelf_location='Estante A-1 · Likod',
            quantity=36,
            days_left=24,
            display_status='healthy',
            display_label='24 araw pa',
            arrival_order=2,
            action_hint='Itabi sa likod hanggang maubos ang mas maagang expiry',
        ),
        SimpleNamespace(
            product=SimpleNamespace(name='Sardinas', unit='cans'),
            batch_code='BT-2026-072',
            shelf_location='Estante B-2',
            quantity=18,
            days_left=60,
            display_status='healthy',
            display_label='60 araw pa',
            arrival_order=1,
            action_hint='Unang dumating sa estante · Ibenta muna',
        ),
    ]
    hero_featured = sellable_batches[0]
    ordered_batches = sorted(sellable_batches, key=lambda batch: batch.arrival_order) if order == 'arrival' else sellable_batches
    return {
        'stock_order': order,
        'is_sample_preview': True,
        'preview_has_summary': True,
        'preview_payment': SimpleNamespace(amount=Decimal('150.00')),
        'preview_hero_featured': hero_featured,
        'preview_customer': SimpleNamespace(
            name='Aling Rosa',
            nickname='Suki sa kanto · Blk 4 Lot 9',
            running_balance=Decimal('200.00'),
        ),
        'preview_entries': [
            SimpleNamespace(
                items_summary='Bigas',
                amount=Decimal('250.00'),
                transaction_type='utang',
                type_label='5 kg Dinorado',
                transaction_date=_sample_time(8, 30),
            ),
            SimpleNamespace(
                items_summary='Mga pinamili',
                amount=Decimal('100.00'),
                transaction_type='utang',
                type_label='Sardinas at sabon',
                transaction_date=_sample_time(11, 15),
            ),
            SimpleNamespace(
                items_summary='Bayad ni Rosa',
                amount=Decimal('150.00'),
                transaction_type='bayad',
                type_label='Bahagyang bayad',
                transaction_date=_sample_time(16, 45),
            ),
        ],
        'preview_featured': ordered_batches[0],
        'preview_other_batches': ordered_batches[1:3],
        'preview_expired': SimpleNamespace(
            product=SimpleNamespace(name='Bear Brand Milk', unit='sachets'),
            display_label='Expired na (4 sachets)',
        ),
        'preview_activity': [
            {'label': 'Cash sale', 'amount': Decimal('120.00'), 'date': _sample_time(7, 15), 'kind': 'Walk-in suki', 'is_payment': False},
            {'label': 'Aling Rosa', 'amount': Decimal('350.00'), 'date': _sample_time(8, 30), 'kind': 'Pautang', 'is_payment': False},
            {'label': 'Bayad ni Rosa', 'amount': Decimal('150.00'), 'date': _sample_time(16, 45), 'kind': 'Bayad sa utang', 'is_payment': True},
        ],
        'preview_summary': {
            'gross_sales': Decimal('470.00'),
            'cash_sales': Decimal('120.00'),
            'utang_sales': Decimal('350.00'),
            'cash_collected': Decimal('270.00'),
            'payments_received': Decimal('150.00'),
        },
        'stock_order_caption': 'Unahin ang unang dumating na batch' if order == 'arrival' else 'Unahin ang pinakamalapit na expiry',
    }


def _public_dashboard_preview():
    """Illustrative in-memory dashboard overview for the public hero frame (0 DB queries)."""
    return {
        'active_nav': 'home',
        'summary': {
            'cash_collected': Decimal('1620.00'),
            'cash_sales': Decimal('1120.00'),
            'payments_received': Decimal('500.00'),
            'uncollected_utang': Decimal('1450.00'),
            'gross_sales': Decimal('1870.00'),
            'gross_profit': Decimal('485.00'),
            'transactions_count': 14,
        },
        'global_store_profile': {
            'store_name': "Aling Nena's Store",
            'owner_name': 'Nena Santos',
            'current_date_display': timezone.localdate().strftime('%d %b %Y'),
        },
        'global_store_kpis': {'overdue_accounts_count': 2},
        'urgent_batches': [
            SimpleNamespace(
                product_id=1,
                product=SimpleNamespace(name='Pancit Canton', unit='pack'),
                quantity=12,
                batch_code='BT-2026-081',
                display_status='expiring_soon',
                display_label='3 days left',
            ),
            SimpleNamespace(
                product_id=2,
                product=SimpleNamespace(name='Sardinas', unit='can'),
                quantity=18,
                batch_code='BT-2026-072',
                display_status='expiring_soon',
                display_label='5 days left',
            ),
        ],
        'overdue_customers': [
            SimpleNamespace(pk=1, name='Aling Rosa', status_label='3 days overdue', running_balance=Decimal('200.00')),
            SimpleNamespace(pk=2, name='Mang Ben', status_label='5 days overdue', running_balance=Decimal('450.00')),
        ],
        'activity': [
            {'label': 'Aling Rosa', 'kind': 'Payment received', 'date': _sample_time(16, 45), 'amount': Decimal('150.00')},
            {'label': 'Aling Rosa', 'kind': 'Utang sale', 'date': _sample_time(8, 30), 'amount': Decimal('350.00')},
            {'label': 'Walk-in customer', 'kind': 'Cash sale', 'date': _sample_time(7, 15), 'amount': Decimal('120.00')},
        ],
    }


def landing_view(request):
    order = 'arrival' if request.GET.get('order') == 'arrival' else 'expiry'
    if request.user.is_authenticated:
        store = current_store(request.user)
        summary, _ = financial_report(store)
        customer = store.customers.order_by('-running_balance', 'name').first()
        batches = [b for b in batches_for(store) if b.quantity > 0 and not b.disposed_at]
        hero_featured = next((b for b in batches if b.display_status in ('expiring_soon', 'healthy')), None)
        if order == 'arrival':
            batches.sort(key=lambda batch: (batch.created_at, batch.pk))
        featured = next((b for b in batches if b.display_status in ('expiring_soon', 'healthy')), None)
        context = {
            'stock_order': order,
            'is_sample_preview': False,
            'preview_has_summary': True,
            'preview_store': store,
            'preview_summary': summary,
            'preview_customer': customer,
            'preview_entries': CustomerLedgerTransaction.objects.filter(customer=customer).order_by('-transaction_date')[:3] if customer else [],
            'preview_batches': batches[:6],
            'preview_sales': SalesTransaction.objects.filter(store=store, transaction_date__gte=period_start('today')).select_related('customer').order_by('-transaction_date')[:3],
            'preview_payment': CustomerLedgerTransaction.objects.filter(customer__store=store, transaction_type='bayad').order_by('-transaction_date').first(),
            'preview_activity': overview_context(store)['activity'][:3],
            'preview_hero_featured': hero_featured,
            'preview_featured': featured,
            'preview_expired': next((b for b in batches if b.display_status == 'expired'), None),
            'stock_order_caption': 'Unahin ang unang dumating na batch' if order == 'arrival' else 'Unahin ang pinakamalapit na expiry',
        }
        context['preview_other_batches'] = [
            b for b in batches if b != featured and b.display_status in ('expiring_soon', 'healthy')
        ][:2]
    else:
        context = _public_landing_preview(order)
    return render(request, 'landing/landing.html', context)


@xframe_options_sameorigin
def dashboard_preview(request):
    """Show the live dashboard design with illustrative sample data publicly, or the signed-in store's records."""
    if request.user.is_authenticated:
        store = request.store = current_store(request.user)
        context = overview_context(store)
    else:
        context = _public_dashboard_preview()
    return render(request, 'home/home.html', context)
